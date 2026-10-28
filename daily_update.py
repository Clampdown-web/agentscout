"""Daily update entry: keep the MCP list_packages snapshot identical to api/products.json.

build_openapi, build_bot_store, and build_seo_new call the same copy on every site build.
Run: python3 daily_update.py
"""
import build_openapi

def main():
    wrote = build_openapi.sync_products_snapshot()
    print("products snapshot:", ", ".join(wrote) if wrote else "already matches api/products.json")

if __name__ == "__main__":
    main()
