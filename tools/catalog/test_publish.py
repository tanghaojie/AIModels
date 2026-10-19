import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from publish import Publication, placement


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True)
        self.base = self.root / 'models/example'
        self.base.mkdir(parents=True)
        self.write_model()
        self.position = {'crs': 'EPSG:4326', 'coordinateSource': 'manifest', 'terrain': 'ellipsoid',
                         'longitude': 104, 'latitude': 30, 'height': 0, 'scale': 1,
                         'heading': 0, 'pitch': 0, 'roll': 0, 'notice': 'Approximate preview position.'}
        self.source = {'version': 1, 'id': 'example', 'label': 'Example', 'description': 'Test asset',
                       'updatedAt': '2026-10-17', 'model': {'url': 'example.glb'}, 'variants': [],
                       'placement': self.position, 'resources': [], 'attribution': []}
        self.save()
        self.track()

    def write_model(self, uri=None):
        data = {'asset': {'version': '2.0'}}
        if uri:
            data['images'] = [{'uri': uri}]
        body = json.dumps(data).encode()
        body += b' ' * (-len(body) % 4)
        (self.base / 'example.glb').write_bytes(struct.pack('<IIIII', 0x46546C67, 2, 20 + len(body),
                                                          len(body), 0x4E4F534A) + body)

    def save(self):
        (self.base / 'model.source.json').write_text(json.dumps(self.source), encoding='utf-8')

    def track(self):
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)

    def test_deterministic_catalog_and_integrity_metadata(self):
        first = Publication(self.root).build()
        self.assertEqual(first, Publication(self.root).build())
        manifest = first[self.base / 'model.json']
        self.assertEqual(manifest['model']['bytes'], (self.base / 'example.glb').stat().st_size)
        self.assertEqual(len(manifest['model']['sha256']), 64)
        self.assertEqual(first[self.root / 'catalog.json']['models'][0]['manifest'],
                         'models/example/model.json')

    def test_nested_missing_texture_rejected(self):
        self.write_model('missing.png')
        with self.assertRaisesRegex(ValueError, 'Missing asset'):
            Publication(self.root).build()

    def test_catalog_order_is_independent_of_platform_path_case_rules(self):
        for folder, key in [('Zebra', 'zebra'), ('alpha', 'alpha')]:
            base = self.root / 'models' / folder
            base.mkdir()
            (base / 'example.glb').write_bytes((self.base / 'example.glb').read_bytes())
            (base / 'model.source.json').write_text(json.dumps({**self.source, 'id': key}), encoding='utf-8')
        self.track()
        catalog = Publication(self.root).build()[self.root / 'catalog.json']
        self.assertEqual([item['id'] for item in catalog['models']], ['alpha', 'example', 'zebra'])

    def test_untracked_texture_rejected(self):
        self.write_model('texture.png')
        (self.base / 'texture.png').write_bytes(b'image')
        with self.assertRaisesRegex(ValueError, 'not tracked'):
            Publication(self.root).build()

    def test_tileset_omission_error_must_be_positive_but_leaf_error_may_be_zero(self):
        tileset = self.base / 'tileset.json'
        data = {'asset': {'version': '1.1'}, 'geometricError': 3000,
                'root': {'boundingVolume': {'sphere': [0, 0, 0, 1500]},
                         'geometricError': 0, 'content': {'uri': 'example.glb'}}}
        self.source['resources'] = [{'id': 'district', 'label': 'District', 'kind': '3d-tiles',
                                     'url': 'tileset.json', 'required': True}]
        self.save()
        tileset.write_text(json.dumps(data), encoding='utf-8')
        self.track()
        Publication(self.root).build()
        for error in (0, -1, None, True, float('inf')):
            with self.subTest(tileset_geometric_error=error):
                tileset.write_text(json.dumps({**data, 'geometricError': error}), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'positive tileset.geometricError'):
                    Publication(self.root).build()

    def test_escaped_and_remote_resources_rejected(self):
        publication = Publication(self.root)
        for url in ('../../../outside.glb', 'https://example.com/model.glb', '/model.glb', '..\\model.glb'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                publication.asset(url, self.base)

    def test_duplicate_variants_rejected(self):
        self.source['variants'] = [{'id': 'balanced', 'label': 'Balanced', 'url': 'example.glb'}] * 2
        self.save()
        with self.assertRaisesRegex(ValueError, 'Duplicate variant'):
            Publication(self.root).build()

    def test_nonfinite_and_missing_coordinates_rejected(self):
        for value in (float('nan'), float('inf'), None, 181, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                placement({**self.position, 'longitude': value})

    def test_undeclared_modes_and_precision_use_static_original(self):
        del self.source['variants']
        self.save()
        outputs = Publication(self.root).build()
        for item in (outputs[self.base / 'model.json'], outputs[self.root / 'catalog.json']['models'][0]):
            self.assertEqual(item['defaultMode'], 'static')
            self.assertEqual(item['defaultVariant'], 'original')
            self.assertEqual(item['modes'], [])
            self.assertEqual(item['variants'], [])

    def test_modes_have_independent_precision_and_integrity(self):
        self.source['variants'] = [{'id': 'balanced', 'label': 'Balanced', 'url': 'example.glb'}]
        self.source['defaultVariant'] = 'balanced'
        self.source['defaultMode'] = 'assembly'
        self.source['modes'] = [
            {'id': 'assembly', 'model': {'url': 'example.glb'}, 'defaultVariant': 'low',
             'variants': [{'id': 'low', 'label': 'Low', 'url': 'example.glb'}]},
            {'id': 'explode', 'model': {'url': 'example.glb'}}]
        self.save()
        outputs = Publication(self.root).build()
        manifest = outputs[self.base / 'model.json']
        catalog = outputs[self.root / 'catalog.json']['models'][0]
        self.assertEqual(manifest['defaultMode'], 'assembly')
        self.assertEqual(catalog['defaultVariant'], 'balanced')
        assembly, explode = manifest['modes']
        self.assertEqual(assembly['model'], manifest['model'])
        self.assertEqual(assembly['defaultVariant'], 'low')
        self.assertEqual(len(assembly['variants'][0]['sha256']), 64)
        self.assertEqual(catalog['modes'][0], {'id': 'assembly', 'label': '飞入拼装',
                         'defaultVariant': 'low', 'variants': [{'id': 'low', 'label': 'Low'}]})
        self.assertEqual(explode['variants'], [])
        self.assertEqual(explode['defaultVariant'], 'original')

    def test_invalid_mode_declarations_rejected(self):
        mode = {'id': 'assembly', 'model': {'url': 'example.glb'}}
        for modes in (None, {}, [mode, mode], [{**mode, 'id': 'static'}],
                      [{**mode, 'id': 'unknown'}], [None], [{**mode, 'model': None}],
                      [{**mode, 'variants': None}]):
            with self.subTest(modes=modes), self.assertRaises(ValueError):
                self.source['modes'] = modes
                self.save()
                Publication(self.root).build()

    def test_invalid_explicit_defaults_rejected(self):
        for fields in ({'defaultMode': 'assembly'}, {'defaultMode': None},
                       {'defaultVariant': 'balanced'}, {'defaultVariant': None},
                       {'modes': [{'id': 'assembly', 'model': {'url': 'example.glb'},
                                   'defaultVariant': 'balanced'}]}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                (self.base / 'model.source.json').write_text(json.dumps({**self.source, **fields}), encoding='utf-8')
                Publication(self.root).build()

    def test_mode_files_and_precision_files_must_exist_and_be_tracked(self):
        (self.base / 'untracked.glb').write_bytes((self.base / 'example.glb').read_bytes())
        for url in ('missing.glb', 'untracked.glb', 'https://example.com/model.glb'):
            for precision in (False, True):
                with self.subTest(url=url, precision=precision), self.assertRaises(ValueError):
                    mode = {'id': 'assembly', 'model': {'url': 'example.glb' if precision else url}}
                    if precision:
                        mode['variants'] = [{'id': 'low', 'label': 'Low', 'url': url}]
                    self.source['modes'] = [mode]
                    self.save()
                    Publication(self.root).build()


if __name__ == '__main__':
    unittest.main()
