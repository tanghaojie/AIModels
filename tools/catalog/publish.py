"""Build and validate the versioned static AIModels publication (stdlib only)."""

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,79}$')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label, maximum=2000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= maximum, f'Invalid {label}')
    return value


def identifier(value):
    require(isinstance(value, str) and ID.fullmatch(value), f'Invalid id: {value}')
    return value


def placement(value):
    require(isinstance(value, dict), 'Missing placement')
    require(value.get('crs') == 'EPSG:4326', 'Unsupported CRS')
    require(value.get('coordinateSource') == 'manifest', 'Explicit manifest coordinates required')
    require(value.get('terrain') in ('ellipsoid', 'any'), 'Unsupported terrain')
    for key, low, high in [('longitude', -180, 180), ('latitude', -90, 90),
                           ('height', -10000, 100000), ('scale', 0.000001, 1000000),
                           ('heading', -360, 360), ('pitch', -360, 360), ('roll', -360, 360)]:
        number = value.get(key)
        require(type(number) in (int, float) and math.isfinite(number) and low <= number <= high,
                f'Invalid placement.{key}')
    text(value.get('notice'), 'placement notice')
    return value


class Publication:
    def __init__(self, root):
        self.root = Path(root).resolve()
        result = subprocess.run(['git', 'ls-files', '-z'], cwd=self.root, check=True, capture_output=True)
        self.tracked = set(result.stdout.decode('utf-8').split('\0'))
        self.visited = set()

    def asset(self, value, base):
        text(value, 'asset URL', 4000)
        parsed = urlsplit(value)
        require(not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.fragment,
                f'Asset must use a relative file URL: {value}')
        require(not parsed.path.startswith('/') and '\\' not in value, f'Invalid asset URL: {value}')
        path = (base / unquote(parsed.path)).resolve()
        require(path.is_relative_to(self.root), f'Asset escapes publication: {value}')
        require(path.is_file(), f'Missing asset: {path}')
        require(path.relative_to(self.root).as_posix() in self.tracked, f'Asset not tracked: {path}')
        return path

    def dependencies(self, path):
        if path in self.visited:
            return
        self.visited.add(path)
        document = None
        if path.suffix.lower() == '.glb':
            with path.open('rb') as stream:
                header = stream.read(20)
                require(len(header) == 20, f'Invalid GLB: {path}')
                magic, version, size, length, kind = struct.unpack('<IIIII', header)
                require(magic == 0x46546C67 and version == 2 and size == path.stat().st_size
                        and kind == 0x4E4F534A and length <= size - 20, f'Invalid GLB: {path}')
                document = json.loads(stream.read(length))
        elif path.suffix.lower() in ('.json', '.gltf'):
            document = json.loads(path.read_text(encoding='utf-8'))
        if document is None:
            return

        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == 'uri' and isinstance(child, str) and not child.startswith('data:'):
                        self.dependencies(self.asset(child, path.parent))
                    else:
                        visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(document)

    def file(self, value, base):
        path = self.asset(value, base)
        require(path.suffix.lower() in ('.glb', '.gltf'), f'Unsupported model: {value}')
        self.dependencies(path)
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        return {'url': value, 'bytes': path.stat().st_size, 'sha256': digest}

    def manifest(self, source):
        data = json.loads(source.read_text(encoding='utf-8'))
        require(data.get('version') == 1, 'Unsupported publication version')
        identifier(data.get('id'))
        text(data.get('label'), 'label', 200)
        text(data.get('description'), 'description')
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', data.get('updatedAt', '')), 'Invalid updatedAt')
        placement(data.get('placement'))
        if data.get('thumbnail'):
            self.asset(data['thumbnail'], source.parent)
        model = self.file(data['model']['url'], source.parent)
        variants = []
        seen = {'original'}
        require(isinstance(data.get('variants'), list) and len(data['variants']) <= 8, 'Invalid variants')
        for variant in data['variants']:
            key = identifier(variant.get('id'))
            require(key not in seen, 'Duplicate variant')
            seen.add(key)
            variants.append({'id': key, 'label': text(variant.get('label'), 'variant label', 200),
                             **self.file(variant['url'], source.parent)})
        resources = data.get('resources')
        require(isinstance(resources, list) and len(resources) <= 16, 'Invalid resources')
        seen = set()
        for resource in resources:
            key = identifier(resource.get('id'))
            require(key not in seen, 'Duplicate resource')
            seen.add(key)
            text(resource.get('label'), 'resource label', 200)
            require(resource.get('kind') in ('3d-tiles', 'geojson'), 'Unsupported resource kind')
            require(type(resource.get('required')) is bool, 'Missing required flag')
            require(type(resource.get('dayNight', False)) is bool, 'Invalid dayNight')
            self.dependencies(self.asset(resource['url'], source.parent))
        credits = data.get('attribution')
        require(isinstance(credits, list) and len(credits) <= 16, 'Invalid attribution')
        for credit in credits:
            text(credit.get('text'), 'attribution')
            parsed = urlsplit(text(credit.get('url'), 'attribution URL', 4000))
            require(parsed.scheme in ('http', 'https') and parsed.netloc and not parsed.username
                    and not parsed.password, 'Invalid attribution URL')
        return {**data, 'model': model, 'variants': variants}

    def build(self):
        outputs = {}
        models = []
        seen = set()
        for source in sorted((self.root / 'models').glob('*/model.source.json')):
            manifest = self.manifest(source)
            key = manifest['id']
            require(key not in seen, f'Duplicate model id: {key}')
            seen.add(key)
            target = source.with_name('model.json')
            outputs[target] = manifest
            entry = {name: manifest[name] for name in ('id', 'label', 'description')}
            entry['manifest'] = target.relative_to(self.root).as_posix()
            entry['variants'] = [{name: variant[name] for name in ('id', 'label')}
                                 for variant in manifest['variants']]
            if manifest.get('thumbnail'):
                entry['thumbnail'] = self.asset(manifest['thumbnail'], source.parent).relative_to(self.root).as_posix()
            models.append(entry)
        require(models, 'No model sources')
        outputs[self.root / 'catalog.json'] = {
            'version': 1, 'updatedAt': max(item['updatedAt'] for item in outputs.values()), 'models': models}
        return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    publication = Publication(ROOT)
    outputs = publication.build()
    for path, data in outputs.items():
        content = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            require(path.is_file() and path.read_text(encoding='utf-8') == content,
                    f'Publication stale: {path}; run python tools/catalog/publish.py')
        else:
            path.write_text(content, encoding='utf-8', newline='\n')
    print(f'Publication {"verified" if args.check else "generated"}: {len(outputs)-1} models; '
          f'{len(publication.visited)} model/dependency files inspected')


if __name__ == '__main__':
    main()
