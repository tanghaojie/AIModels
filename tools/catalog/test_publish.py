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

    def test_untracked_texture_rejected(self):
        self.write_model('texture.png')
        (self.base / 'texture.png').write_bytes(b'image')
        with self.assertRaisesRegex(ValueError, 'not tracked'):
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


if __name__ == '__main__':
    unittest.main()
