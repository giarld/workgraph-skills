#!/usr/bin/env python3
"""Discover provider models and generate images. Python 3.8+ standard library only."""

import argparse
import base64
import binascii
from datetime import datetime, timezone
import http.client
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

BASE_ENV = 'IMAGEGEN_OPENAI_API_BASE_URL'
KEY_ENV = 'IMAGEGEN_OPENAI_API_KEY'
DEFAULT_BASE = 'https://api.openai.com/v1'
FAMILIES = ('gpt-image-2.5-sunburst', 'gpt-image-2.5-flare',
            'gpt-image-2', 'gpt-image-1.5')
FIELDS = {'model', 'prompt', 'n', 'size', 'quality', 'output_format',
          'background', 'output_compression', 'moderation', 'safety_identifier'}
MAX_RESPONSE_BYTES = 256 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def http_url(value):
    require(isinstance(value, str) and value and not any(c.isspace() for c in value),
            'Expected a nonempty HTTP(S) URL without whitespace')
    parsed = urllib.parse.urlsplit(value)
    require(parsed.scheme in ('http', 'https') and parsed.hostname
            and parsed.username is None and parsed.password is None,
            'Expected an HTTP(S) URL without embedded credentials')
    parsed.port  # Validate malformed port numbers before sending credentials.
    return parsed


def api_base():
    value = os.environ.get(BASE_ENV, DEFAULT_BASE).strip().rstrip('/')
    parsed = http_url(value)
    require(not parsed.query and not parsed.fragment,
            BASE_ENV + ' must not contain a query or fragment')
    return value


def api_key():
    value = os.environ.get(KEY_ENV, '').strip()
    require(value and not any(c.isspace() for c in value),
            'Set ' + KEY_ENV + ' in the execution environment')
    return value


def sanitized(value):
    text = str(value)
    key = os.environ.get(KEY_ENV, '').strip()
    return text.replace(key, '[REDACTED]') if key else text


def known_family(model):
    tail = model.rsplit('/', 1)[-1]
    for family in FAMILIES:
        if tail == family or re.fullmatch(re.escape(family) + r'-\d{4}-\d{2}-\d{2}', tail):
            return family
    return None


def validate(body):
    require(isinstance(body, dict), 'Request must be a JSON object')
    require(set(body) <= FIELDS, 'Request contains unsupported fields; see references/api.md')
    require(isinstance(body.get('model'), str) and body['model'].strip(),
            'An explicit provider model ID is required')
    prompt = body.get('prompt')
    require(isinstance(prompt, str) and prompt.strip() and len(prompt) <= 32000,
            'prompt must contain 1–32000 characters')
    body = dict(body)
    body.setdefault('n', 1)
    body.setdefault('output_format', 'png')
    require(type(body['n']) is int and 1 <= body['n'] <= 10, 'n must be an integer from 1 to 10')
    require(body['output_format'] in ('png', 'jpeg', 'webp'), 'Invalid output_format')
    require(body.get('background', 'auto') in ('auto', 'opaque', 'transparent'), 'Invalid background')
    require(body.get('background') != 'transparent' or body['output_format'] in ('png', 'webp'),
            'Transparent backgrounds require PNG or WebP')
    if 'output_compression' in body:
        require(type(body['output_compression']) is int and 0 <= body['output_compression'] <= 100
                and body['output_format'] in ('jpeg', 'webp'),
                'output_compression requires JPEG/WebP and an integer from 0 to 100')
    require(body.get('moderation', 'auto') in ('auto', 'low'), 'Invalid moderation')
    if 'safety_identifier' in body:
        value = body['safety_identifier']
        require(isinstance(value, str) and value.strip() and len(value) <= 128,
                'safety_identifier must contain 1–128 characters')
    family = known_family(body['model'])
    quality = body.get('quality', 'auto')
    require(isinstance(quality, str) and quality.strip(), 'quality must be a nonempty string')
    if family:
        qualities = {'auto', 'low', 'medium', 'high'}
        if family.startswith('gpt-image-2.5-'):
            qualities |= {'xhigh', 'max'}
        require(quality in qualities, 'Unsupported quality for the known model family')
    size = body.get('size', 'auto')
    require(isinstance(size, str), 'size must be auto or WIDTHxHEIGHT')
    if size != 'auto':
        match = re.fullmatch(r'([1-9]\d{0,5})x([1-9]\d{0,5})', size)
        require(match is not None, 'size must be auto or WIDTHxHEIGHT')
        width, height = map(int, match.groups())
        if family == 'gpt-image-1.5':
            require(size in ('1024x1024', '1536x1024', '1024x1536'),
                    'Unsupported size for gpt-image-1.5')
        elif family:
            require(width % 16 == 0 and height % 16 == 0
                    and width <= 3 * height and height <= 3 * width,
                    'Known GPT Image 2/2.5 sizes need multiples of 16 and aspect ratio 1:3–3:1')
            if family.startswith('gpt-image-2.5-'):
                require(max(width, height) <= 3840 and 655360 <= width * height <= 8294400,
                        'GPT Image 2.5 size exceeds its pixel or edge limits')
    return body


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def read_limited(response):
    declared = response.headers.get('Content-Length')
    if declared is not None:
        require(0 <= int(declared) <= MAX_RESPONSE_BYTES, 'Invalid or oversized response Content-Length')
    data = response.read(MAX_RESPONSE_BYTES + 1)
    require(len(data) <= MAX_RESPONSE_BYTES, 'Response exceeds the helper limit of 256 MiB')
    require(declared is None or len(data) == int(declared), 'Incomplete HTTP response; no automatic retry')
    return data


def request_json(base, key, method, path, timeout, body=None):
    payload = None if body is None else json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
    req = urllib.request.Request(base + path, data=payload, method=method, headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            request_id = response.headers.get('x-request-id', '')
            result = json.loads(read_limited(response))
    except urllib.error.HTTPError as exc:
        request_id = exc.headers.get('x-request-id', '')
        try:
            error = json.loads(exc.read(65536)).get('error', {})
            detail = error.get('message', '') if isinstance(error, dict) else str(error)
            code = error.get('code', '') if isinstance(error, dict) else ''
        except (ValueError, AttributeError):
            detail, code = 'Non-JSON error response', ''
        raise RuntimeError(sanitized('API HTTP {}; code={}; {}; request_id={}'.format(
            exc.code, code, detail, request_id))[:2000]) from None
    require(isinstance(result, dict), 'API must return a JSON object')
    require(not result.get('error'), 'API returned an error object; no automatic retry')
    return result, request_id


def list_models(base, key, timeout):
    rows, seen_ids, cursors = [], set(), set()
    path = '/models'
    for _ in range(100):
        result, _ = request_json(base, key, 'GET', path, timeout)
        page = result.get('data')
        require(isinstance(page, list), 'Model response must contain a data array')
        for row in page:
            require(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id'].strip(),
                    'Model response contains an invalid model ID')
            if row['id'] not in seen_ids:
                rows.append(row)
                seen_ids.add(row['id'])
        if not result.get('has_more'):
            return rows
        cursor = result.get('last_id') or (page[-1]['id'] if page else None)
        require(isinstance(cursor, str) and cursor and cursor not in cursors,
                'Model pagination did not advance; refusing an incomplete catalog')
        cursors.add(cursor)
        path = '/models?' + urllib.parse.urlencode({'after': cursor})
    raise ValueError('Model pagination exceeded 100 pages; refusing an incomplete catalog')


def new_run(output_dir):
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = 'imagegen-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
    return Path(tempfile.mkdtemp(prefix=prefix, dir=str(output_dir)))


def write_json(path, data):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def store_response(response, run_dir, model=None, request_id=''):
    write_json(run_dir / 'response-meta.json', {'model': model or response.get('model'),
                                              'request_id': request_id})
    write_json(run_dir / 'response.json', response)


def image_format(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    raise ValueError('Returned data is not a recognized PNG, JPEG, or WebP image')


def image_bytes(item, timeout):
    require(isinstance(item, dict), 'Each response image must be an object')
    encoded = item.get('b64_json')
    if isinstance(encoded, str) and encoded:
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('Invalid image base64 in response') from None
    url = item.get('url')
    http_url(url)
    # Keep redirects disabled, including for downloads, to reject unvalidated URL schemes.
    # These requests deliberately have no Authorization header.
    with urllib.request.build_opener(NoRedirect()).open(
            urllib.request.Request(url, headers={'Accept': 'image/*'}), timeout=timeout) as response:
        return read_limited(response)


def save_images(response, run_dir, timeout, model=None, request_id=''):
    data = response.get('data')
    require(isinstance(data, list) and data, 'Response contains no images; do not automatically regenerate')
    manifest = {'model': model or response.get('model'), 'request_id': request_id,
                'run_dir': str(run_dir), 'response_file': str(run_dir / 'response.json'), 'images': []}
    manifest['metadata'] = {key: response[key] for key in
                            ('created', 'size', 'quality', 'background', 'output_format', 'usage') if key in response}
    for index, item in enumerate(data, 1):
        content = image_bytes(item, timeout)
        fmt = image_format(content)
        path = run_dir / ('image-{:02d}.{}'.format(index, fmt))
        with path.open('xb') as handle:
            handle.write(content)
        manifest['images'].append({'path': str(path), 'format': fmt, 'bytes': len(content)})
    write_json(run_dir / 'manifest.json', manifest)
    return manifest


def load_json(path):
    def reject_constant(value):
        raise ValueError('Non-finite numbers are not valid JSON')
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)


def run(args):
    require(math.isfinite(args.timeout) and args.timeout > 0, 'timeout must be positive and finite')
    if args.command == 'models':
        base = api_base()
        rows = list_models(base, api_key(), args.timeout)
        return {'models': [dict(row, skill_known_profile=known_family(row['id']),
                                skill_image_candidate=bool(known_family(row['id'])
                                                           or 'image' in row['id'].lower())) for row in rows]}
    if args.command == 'save':
        response = load_json(args.response)
        require(isinstance(response, dict), 'Stored response must be a JSON object')
        meta_path = args.response.with_name(args.response.stem + '-meta.json')
        context = load_json(meta_path) if meta_path.exists() else {}
        require(isinstance(context, dict) and set(context) <= {'model', 'request_id'}
                and (context.get('model') is None or isinstance(context['model'], str))
                and isinstance(context.get('request_id', ''), str), 'Invalid response metadata sidecar')
        run_dir = new_run(args.output_dir)
        store_response(response, run_dir, **context)
        print(json.dumps({'stage': 'saving', 'run_dir': str(run_dir)}), file=sys.stderr, flush=True)
        return save_images(response, run_dir, args.timeout, **context)
    body = validate(load_json(args.json))
    base = api_base()
    if args.dry_run:
        return {'dry_run': True, 'method': 'POST', 'url': base + '/images/generations',
                'model': body['model'], 'known_profile': known_family(body['model']),
                'n': body['n'], 'output_format': body['output_format'],
                'size': body.get('size', 'auto'), 'quality': body.get('quality', 'auto'),
                'model_availability_checked': False}
    key = api_key()
    models = list_models(base, key, min(args.timeout, 30))
    require(any(row['id'] == body['model'] for row in models),
            'Selected model is absent from the fresh provider catalog; no generation submitted')
    run_dir = new_run(args.output_dir)
    write_json(run_dir / 'request.json', body)
    print(json.dumps({'stage': 'generating', 'model': body['model'], 'run_dir': str(run_dir)}),
          file=sys.stderr, flush=True)
    response, request_id = request_json(base, key, 'POST', '/images/generations', args.timeout, body)
    store_response(response, run_dir, body['model'], request_id)
    try:
        return save_images(response, run_dir, args.timeout, body['model'], request_id)
    except (ValueError, OSError, http.client.HTTPException) as exc:
        raise RuntimeError('Image retrieval failed: {}. Recover using save --response {} instead of regenerating'.format(
            sanitized(exc), run_dir / 'response.json')) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    models = sub.add_parser('models', help='Fetch every provider model with advisory image annotations')
    models.add_argument('--timeout', type=float, default=30)
    generate = sub.add_parser('generate', help='Refresh model availability and generate images once')
    generate.add_argument('--json', required=True, type=Path)
    generate.add_argument('--output-dir', required=True, type=Path)
    generate.add_argument('--timeout', type=float, default=300)
    generate.add_argument('--dry-run', action='store_true')
    save = sub.add_parser('save', help='Save images from a stored response without generating again')
    save.add_argument('--response', required=True, type=Path)
    save.add_argument('--output-dir', required=True, type=Path)
    save.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    try:
        result = run(args)
        print(sanitized(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)))
        return 0
    except (ValueError, OSError, RuntimeError, http.client.HTTPException) as exc:
        message = sanitized(exc)
        if args.command == 'generate' and not args.dry_run:
            message += '; no automatic retry. A submitted POST may have incurred a charge.'
        print(json.dumps({'error': message}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
