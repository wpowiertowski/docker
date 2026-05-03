import aiohttp
from .config import Config


async def get_registration_token(cfg: Config) -> str:
    owner, repo = cfg.github_repo.split("/", 1)
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runners/registration-token"
    headers = {
        "Authorization": f"Bearer {cfg.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["token"]
