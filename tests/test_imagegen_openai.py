"""Local provider integration tests; no external service or paid generation."""

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/imagegen-openai/scripts/imagegen.py'
SPEC = importlib.util.spec_from_file_location('imagegen', SCRIPT)
IMAGEGEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMAGEGEN)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=')
FAKE_KEY = 'local-test-key-never-a-real-credential'


class Provider(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, payload, headers=None):
        data = json.dumps(payload).encode() if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('x-request-id', 'local-request-id')
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.server.events.append(('GET', self.path, self.headers.get('Authorization'), None))
        if self.path.startswith('/gateway/v1/models'):
            if self.server.discovery_status != 200:
                return self.reply(self.server.discovery_status, {'error': {'message': 'Discovery failed'}})
            if self.server.redirect_models:
                return self.reply(302, {}, {'Location': self.server.base + '/stolen'})
            if self.server.pages:
                index = 1 if '?' in self.path else 0
                return self.reply(200, self.server.pages[index])
            return self.reply(200, {'data': self.server.models})
        if self.path == '/image.png':
            return self.reply(200, PNG)
        if self.path == '/partial.png':
            self.send_response(200)
            self.send_header('Content-Length', str(len(PNG) + 10))
            self.end_headers()
            self.wfile.write(PNG)
            self.close_connection = True
            return
        return self.reply(404, {'error': {'message': 'Not found'}})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.events.append(('POST', self.path, self.headers.get('Authorization'), body))
        if self.server.generation_status != 200:
            return self.reply(self.server.generation_status, {'error': {
                'code': 'test_failure', 'message': 'Echoed credential: ' + FAKE_KEY}})
        if self.server.generation_redirect:
            return self.reply(307, {}, {'Location': self.server.base + '/stolen'})
        self.reply(200, self.server.result)


class ImageGenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
        cls.server.base = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'outputs'
        self.request = self.root / 'request.json'
        self.server.events = []
        self.server.models = [{'id': family} for family in IMAGEGEN.FAMILIES]
        self.server.pages = []
        self.server.discovery_status = 200
        self.server.generation_status = 200
        self.server.redirect_models = False
        self.server.generation_redirect = False
        self.server.result = {'data': [{'b64_json': base64.b64encode(PNG).decode()}],
                              'size': '1024x1024', 'quality': 'medium', 'usage': {'total_tokens': 10}}
        self.env = {IMAGEGEN.BASE_ENV: self.server.base + '/gateway/v1/', IMAGEGEN.KEY_ENV: FAKE_KEY}

    def cli(self, *args, expected=0, env=None):
        proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              env=self.env if env is None else env,
                              text=True, capture_output=True, timeout=15)
        self.assertEqual(proc.returncode, expected, proc.stderr)
        self.assertNotIn(FAKE_KEY, proc.stdout + proc.stderr)
        return proc

    def generate(self, model='gpt-image-2.5-flare', expected=0, dry=False, **extra):
        body = {'model': model, 'prompt': '水彩狐狸，不要文字。'}
        body.update(extra)
        self.request.write_text(json.dumps(body, ensure_ascii=False), encoding='utf-8')
        args = ['generate', '--json', self.request, '--output-dir', self.output]
        if dry:
            args.append('--dry-run')
        return self.cli(*args, expected=expected)

    def test_discovery_keeps_unknown_and_non_image_named_models(self):
        self.server.models += [{'id': 'future-image-9'}, {'id': 'art-engine', 'modalities': ['image']},
                               {'id': 'text-model'}]
        rows = json.loads(self.cli('models').stdout)['models']
        self.assertEqual([row['id'] for row in rows], [row['id'] for row in self.server.models])
        self.assertEqual(rows[0]['skill_known_profile'], 'gpt-image-2.5-sunburst')
        self.assertIsNone(rows[4]['skill_known_profile'])
        self.assertTrue(rows[4]['skill_image_candidate'])
        self.assertEqual(rows[5]['modalities'], ['image'])
        self.assertFalse(rows[6]['skill_image_candidate'])
        self.assertEqual(self.server.events[0][1:3], ('/gateway/v1/models', 'Bearer ' + FAKE_KEY))

    def test_all_four_known_models_generate_after_discovery(self):
        for family in IMAGEGEN.FAMILIES:
            with self.subTest(family=family):
                self.server.events = []
                result = json.loads(self.generate(model=family).stdout)
                self.assertEqual([event[0] for event in self.server.events], ['GET', 'POST'])
                self.assertEqual(self.server.events[1][1], '/gateway/v1/images/generations')
                self.assertEqual(self.server.events[1][3]['model'], family)
                self.assertEqual(result['model'], family)
                image = Path(result['images'][0]['path'])
                self.assertTrue(image.is_absolute())
                self.assertEqual(image.read_bytes(), PNG)
                self.assertEqual(result['request_id'], 'local-request-id')
                self.assertEqual(result['metadata']['usage'], {'total_tokens': 10})
                self.assertTrue((image.parent / 'request.json').is_file())
                self.assertTrue((image.parent / 'response.json').is_file())
                self.assertTrue((image.parent / 'response-meta.json').is_file())
                self.assertTrue((image.parent / 'manifest.json').is_file())
                self.assertEqual(self.server.events[1][3]['prompt'], '水彩狐狸，不要文字。')

    def test_unknown_model_with_non_image_name_is_selectable(self):
        self.server.models = [{'id': 'art-engine'}]
        result = json.loads(self.generate(model='art-engine', size='777x555', quality='ultra').stdout)
        self.assertEqual(result['model'], 'art-engine')

    def test_exact_namespaced_snapshot_preserved(self):
        model = 'vendor/gpt-image-2.5-flare-2026-09-08'
        self.server.models = [{'id': model}]
        result = json.loads(self.generate(model=model, quality='max').stdout)
        self.assertEqual(result['model'], model)
        self.assertEqual(IMAGEGEN.known_family(model), 'gpt-image-2.5-flare')
        self.assertIsNone(IMAGEGEN.known_family('gpt-image-2.5-flare-other'))

    def test_catalog_refreshed_when_model_removed(self):
        self.cli('models')
        self.server.models = [{'id': 'gpt-image-2'}]
        self.generate(expected=1)
        self.assertEqual([event[0] for event in self.server.events], ['GET', 'GET'])
        self.assertFalse(self.output.exists())

    def test_failed_discovery_does_not_submit(self):
        self.server.discovery_status = 503
        self.generate(expected=1)
        self.assertEqual([event[0] for event in self.server.events], ['GET'])
        self.assertFalse(self.output.exists())

    def test_pagination_reaches_unknown_model(self):
        self.server.pages = [{'data': [{'id': 'text-model'}], 'has_more': True, 'last_id': 'text-model'},
                             {'data': [{'id': 'future-image'}], 'has_more': False}]
        self.generate(model='future-image')
        self.assertEqual([event[1] for event in self.server.events],
                         ['/gateway/v1/models', '/gateway/v1/models?after=text-model',
                          '/gateway/v1/images/generations'])

    def test_repeating_pagination_fails_closed(self):
        page = {'data': [{'id': 'gpt-image-2.5-flare'}], 'has_more': True, 'last_id': 'same'}
        self.server.pages = [page, page]
        self.generate(expected=1)
        self.assertEqual(len(self.server.events), 2)
        self.assertTrue(all(event[0] == 'GET' for event in self.server.events))

    def test_dry_run_without_key_makes_no_requests_or_outputs(self):
        self.env.pop(IMAGEGEN.KEY_ENV)
        result = json.loads(self.generate(dry=True).stdout)
        self.assertFalse(result['model_availability_checked'])
        self.assertEqual(result['url'], self.server.base + '/gateway/v1/images/generations')
        self.assertEqual(self.server.events, [])
        self.assertFalse(self.output.exists())

    def test_missing_key_fails_before_network(self):
        self.env.pop(IMAGEGEN.KEY_ENV)
        self.generate(expected=1)
        self.assertEqual(self.server.events, [])

    def test_invalid_base_does_not_fallback(self):
        for value in ('', 'ftp://example.com', 'https://user:pass@example.com/v1',
                      'https://example.com/v1?key=value', 'https://example.com/v1#fragment'):
            with self.subTest(value=value):
                self.env[IMAGEGEN.BASE_ENV] = value
                self.generate(expected=1, dry=True)
                self.assertEqual(self.server.events, [])

    def test_default_base_has_one_version_segment(self):
        self.env.pop(IMAGEGEN.BASE_ENV)
        result = json.loads(self.generate(dry=True).stdout)
        self.assertEqual(result['url'], 'https://api.openai.com/v1/images/generations')

    def test_generation_failure_does_not_retry_or_leak_key(self):
        self.server.generation_status = 429
        proc = self.generate(expected=1)
        self.assertIn('API HTTP 429', proc.stderr)
        self.assertIn('local-request-id', proc.stderr)
        self.assertIn('[REDACTED]', proc.stderr)
        self.assertEqual([event[0] for event in self.server.events], ['GET', 'POST'])
        self.assertEqual(len(list(self.output.glob('*/request.json'))), 1)

    def test_authenticated_redirect_is_not_followed(self):
        self.server.redirect_models = True
        self.generate(expected=1)
        self.assertEqual(len(self.server.events), 1)

    def test_post_redirect_is_not_resubmitted(self):
        self.server.generation_redirect = True
        self.generate(expected=1)
        self.assertEqual([event[0] for event in self.server.events], ['GET', 'POST'])

    def test_url_download_has_no_authorization(self):
        self.server.result = {'data': [{'url': self.server.base + '/image.png'}]}
        result = json.loads(self.generate().stdout)
        self.assertEqual(Path(result['images'][0]['path']).read_bytes(), PNG)
        self.assertEqual(self.server.events[-1][1:3], ('/image.png', None))

    def test_failed_download_can_recover_without_generation_or_key(self):
        self.server.result = {'data': [{'url': self.server.base + '/missing.png'}]}
        proc = self.generate(expected=1)
        self.assertIn('Recover using save', proc.stderr)
        response = next(self.output.glob('*/response.json'))
        # Simulate obtaining a fresh result URL from provider records after expiry.
        response.write_text(json.dumps({'data': [{'url': self.server.base + '/image.png'}]}))
        self.env.pop(IMAGEGEN.KEY_ENV)
        self.env[IMAGEGEN.BASE_ENV] = 'invalid-base-not-needed-for-recovery'
        self.server.events = []
        result = json.loads(self.cli('save', '--response', response, '--output-dir', self.output).stdout)
        self.assertEqual(Path(result['images'][0]['path']).read_bytes(), PNG)
        self.assertEqual(result['model'], 'gpt-image-2.5-flare')
        self.assertEqual(result['request_id'], 'local-request-id')
        copied_context = Path(result['run_dir']) / 'response-meta.json'
        self.assertEqual(json.loads(copied_context.read_text()),
                         {'model': 'gpt-image-2.5-flare', 'request_id': 'local-request-id'})
        self.assertEqual([event[0] for event in self.server.events], ['GET'])
        self.assertIsNone(self.server.events[0][2])

    def test_truncated_download_preserves_response_without_regenerating(self):
        self.server.result = {'data': [{'url': self.server.base + '/partial.png'}]}
        proc = self.generate(expected=1)
        self.assertIn('Incomplete HTTP response', proc.stderr)
        self.assertIn('Recover using save', proc.stderr)
        self.assertEqual([event[0] for event in self.server.events], ['GET', 'POST', 'GET'])
        self.assertEqual(len(list(self.output.glob('*/response.json'))), 1)
        self.assertEqual(len(list(self.output.glob('*/image-*'))), 0)

    def test_base64_save_is_offline_and_does_not_overwrite(self):
        response = self.root / 'response.json'
        response.write_text(json.dumps(self.server.result))
        self.env.clear()
        results = [json.loads(self.cli('save', '--response', response, '--output-dir', self.output).stdout)
                   for _ in range(2)]
        self.assertNotEqual(results[0]['run_dir'], results[1]['run_dir'])
        self.assertEqual(self.server.events, [])

    def test_invalid_images_preserve_response_for_recovery(self):
        for data in ({'b64_json': 'not base64!'},
                     {'b64_json': base64.b64encode(b'<html>not an image</html>').decode()},
                     {'url': 'file:///etc/passwd'}):
            with self.subTest(data=data):
                self.server.result = {'data': [data]}
                self.generate(expected=1)
        self.assertEqual(len(list(self.output.glob('*/response.json'))), 3)
        self.assertEqual(len(list(self.output.glob('*/image-*'))), 0)

    def test_encoding_detection_uses_actual_bytes(self):
        self.assertEqual(IMAGEGEN.image_format(PNG), 'png')
        self.assertEqual(IMAGEGEN.image_format(b'\xff\xd8\xff\xe0test'), 'jpeg')
        self.assertEqual(IMAGEGEN.image_format(b'RIFF1234WEBPtest'), 'webp')

    def test_multiple_images_are_all_saved(self):
        self.server.result['data'] *= 2
        result = json.loads(self.generate(n=2).stdout)
        self.assertEqual(len(result['images']), 2)
        self.assertNotEqual(result['images'][0]['path'], result['images'][1]['path'])

    def test_known_family_parameter_limits_before_network(self):
        cases = [dict(quality='max', model='gpt-image-2'),
                 dict(quality='xhigh', model='gpt-image-1.5'),
                 dict(size='1536x864', model='gpt-image-1.5'),
                 dict(size='1000x1000'), dict(size='512x512'), dict(size='4096x2048'),
                 dict(size='3840x3840'), dict(size='3072x768'),
                 dict(background='transparent', output_format='jpeg'),
                 dict(output_compression=50), dict(n=True), dict(n=11), dict(prompt=''),
                 dict(response_format='b64_json'), dict(stream=True)]
        for case in cases:
            with self.subTest(case=case):
                self.generate(expected=1, **case)
        self.assertEqual(self.server.events, [])

    def test_valid_custom_sizes_and_quality(self):
        for size in ('1536x864', '3840x2160', '2160x3840'):
            self.generate(dry=True, size=size, quality='max', background='transparent')
        self.generate(model='gpt-image-2', size='1536x864', quality='high', dry=True)
        self.assertEqual(self.server.events, [])

    def test_bad_timeout_rejected_without_network(self):
        for value in ('0', '-1', 'nan', 'inf'):
            self.cli('models', '--timeout', value, expected=1)
        self.assertEqual(self.server.events, [])


if __name__ == '__main__':
    unittest.main()
