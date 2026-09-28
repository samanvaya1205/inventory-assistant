import httpx
from langchain_core.tools import tool

API_URL = "http://127.0.0.1:8000/api"

def login(username, password):
    """get a jwt access token from the django API."""
    r = httpx.post(f"{API_URL}/token/", json={"username": username, "password": password})
    r.raise_for_status()
    return r.json()["access"]

def make_read_tools(token):
    """build read-only tools that call the APIU as the logged in user."""
    headers = {"Authorization": f"Bearer {token}"}

    def api_get(path):
        r = httpx.get(f"{API_URL}/{path}", headers=headers, timeout=10)
        if r.status_code in (401, 403, 404):
            return {"error": r.status_code, "detail": r.json().get("detail", "")}
        r.raise_for_status()
        return r.json()


    @tool
    def list_items():
        """list every inventory item with its prioce, stock status, category and tags."""
        return api_get("items/")
    
    @tool
    def get_item(item_id: int):
        """Get one inventory item by its numeric id."""
        return api_get(f"items/{item_id}/")

    @tool
    def list_categories():
        """list all item categories."""
        return api_get("categories/")

    @tool
    def list_tags():
        """list all item tags."""
        return api_get("tags/")


    return[list_items, get_item, list_categories, list_tags]

def make_write_tools(token):
    """Build tools that change data. The API decides whether this user may use them."""
    headers = {"Authorization": f"Bearer {token}"}

    def api_send(method, path, data=None):
        r = httpx.request(method, f"{API_URL}/{path}", headers=headers, json=data, timeout=10)
        if r.status_code == 204:
            return {"ok": True}
        if r.status_code >= 400:
            try:
                detail = r.json()
            except ValueError:
                detail = r.text
            return {"error": r.status_code, "detail": detail}
        return r.json()

    @tool
    def create_item(name: str, price: float, category: str | None = None,
                    tags: list[str] | None = None, in_stock: bool = True):
        """Create a new inventory item. category and tags are names, e.g. "accessories" and ["sale"]."""
        data = {"name": name, "price": price, "in_stock": in_stock,
                "category": category, "tags": tags or []}
        return api_send("POST", "items/", data)

    @tool
    def update_item(item_id: int, name: str | None = None, price: float | None = None,
                    in_stock: bool | None = None, category: str | None = None,
                    tags: list[str] | None = None):
        """Change an existing item by id. Only pass the fields that should change."""
        changes = {"name": name, "price": price, "in_stock": in_stock,
                   "category": category, "tags": tags}
        data = {k: v for k, v in changes.items() if v is not None}
        return api_send("PATCH", f"items/{item_id}/", data)

    @tool
    def delete_item(item_id: int):
        """Delete an item by id. Find the id first with list_items."""
        return api_send("DELETE", f"items/{item_id}/")

    @tool
    def create_category(name: str):
        """Create a new category."""
        return api_send("POST", "categories/", {"name": name})

    @tool
    def create_tag(name: str):
        """Create a new tag."""
        return api_send("POST", "tags/", {"name": name})

    return [create_item, update_item, delete_item, create_category, create_tag]