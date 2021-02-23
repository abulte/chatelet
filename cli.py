from aiohttp.test_utils import TestClient, TestServer
from minicli import cli, run

from chatelet.app import app


@cli
async def apidoc():
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/api/docs/swagger.json")
        assert resp.status == 200
        with open("docs/swagger.json", "w") as f:
            f.write(await resp.text())


if __name__ == "__main__":
    run()
