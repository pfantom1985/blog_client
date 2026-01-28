from __future__ import annotations

import argparse
import json
from typing import Any

from pydantic import TypeAdapter, ValidationError
from blog_client.client import APIClient, APIClientError
from blog_client.models import PostWithComments
from blog_client.storage import read_json, write_json
from blog_client.utils import EXIT_INPUT_ERROR, EXIT_OK, EXIT_RUNTIME_ERROR, dump_jsonable

def cmd_posts(args: argparse.Namespace) -> int:
    with APIClient(timeout=args.timeout) as client:
        posts = [dump_jsonable(p) for p in client.iter_all_posts(limit=args.limit)]
        write_json(args.out, posts)
        print(f"Saved {len(posts)} posts to {args.out}")
        return EXIT_OK

def cmd_post(args: argparse.Namespace) -> int:
    out_path = args.out or f"post_{args.id}.json"

    with APIClient(timeout=args.timeout) as client:
        post = client.get_post(args.id)
        comments = client.get_comments_for_post(args.id)
        payload = dump_jsonable(PostWithComments(post=post, comments=comments))
        write_json(out_path, payload)
        print(f"Saved post {args.id} with {len(payload['comments'])} comments to {out_path}")
        return EXIT_OK

def cmd_export(args: argparse.Namespace) -> int:
    with APIClient(timeout=args.timeout) as client:
        items: list[dict[str, Any]] = []
        for post in client.iter_all_posts(limit=args.limit):
            comments = client.get_comments_for_post(post.id)
            items.append(dump_jsonable(PostWithComments(post=post, comments=comments)))
        write_json(args.out, items)
        print(f"Saved export ({len(items)} posts) to {args.out}")
        return EXIT_OK

def cmd_stats(args: argparse.Namespace) -> int:
    try:
        raw = read_json(args.out)
    except FileNotFoundError:
        print(f"Файл не найден: {args.out}. Сначала запустите export.")
        return EXIT_INPUT_ERROR
    except json.JSONDecodeError:
        print(f"Файл повреждён (не JSON): {args.out}. Пересоздайте через export.")
        return EXIT_INPUT_ERROR

    adapter = TypeAdapter(list[PostWithComments])
    try:
        items = adapter.validate_python(raw)
    except ValidationError as e:
        print("Файл имеет неожиданную структуру (валидация не прошла).")
        print(e)
        return EXIT_INPUT_ERROR
    posts_count = len(items)
    comments_total = sum(len(x.comments) for x in items)
    avg = (comments_total / posts_count) if posts_count else 0.0
    top5 = sorted(items, key=lambda x: len(x.comments), reverse=True)[:5]
    print(f"Posts: {posts_count}")
    print(f"Avg comments per post: {avg:.2f}")
    print("Top-5 posts by comments:")
    for x in top5:
        print(f" id={x.post.id} count={len(x.comments)}")
    return EXIT_OK

def cmd_selfcheck(args: argparse.Namespace) -> int:
    with APIClient(base_url=args.selfcheck_url, timeout=args.timeout) as client:
        # Важно: /unstable может возвращать не-JSON, поэтому selfcheck не должен вызывать request_json()
        client.request("GET", "/unstable")
        print("Selfcheck OK (request eventually succeeded).")
        return EXIT_OK

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="blog_client")

    parser.add_argument("--timeout", type=float, default=10.0)

    sub = parser.add_subparsers(dest="command", required=True)  # [web:202]

    p_posts = sub.add_parser("posts", help="Download all posts with pagination.")
    p_posts.add_argument("--limit", type=int, default=10)
    p_posts.add_argument("--out", default="posts.json")
    p_posts.set_defaults(func=cmd_posts)  # dispatch-паттерн [web:202]

    p_post = sub.add_parser("post", help="Download one post and its comments.")
    p_post.add_argument("id", type=int)
    p_post.add_argument("--out", default=None)
    p_post.set_defaults(func=cmd_post)  # [web:202]

    p_export = sub.add_parser("export", help="Download all posts + comments and save to export.json.")
    p_export.add_argument("--limit", type=int, default=10)
    p_export.add_argument("--out", default="export.json")
    p_export.set_defaults(func=cmd_export)  # [web:202]

    p_stats = sub.add_parser("stats", help="Show stats from export.json.")
    p_stats.add_argument("--out", default="export.json")
    p_stats.set_defaults(func=cmd_stats)  # [web:202]

    p_self = sub.add_parser("selfcheck", help="Test retries using httpbin.dev/unstable.")
    p_self.add_argument("--selfcheck-url", default="https://httpbin.dev")
    p_self.set_defaults(func=cmd_selfcheck)  # [web:202]

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.func(args)
    except APIClientError as e:
        print(f"Ошибка: {e}")
        code = EXIT_RUNTIME_ERROR
    raise SystemExit(code)
