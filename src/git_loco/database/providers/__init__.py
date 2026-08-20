from git_loco.database.providers.d1 import D1Provider
from git_loco.errors import ProviderError

PROVIDERS: dict[str, type] = {"d1": D1Provider}


def get_provider(name: str) -> type:
    try:
        return PROVIDERS[name]
    except KeyError:
        raise ProviderError(
            f"Unknown provider '{name}'. Available: {', '.join(sorted(PROVIDERS))}"
        ) from None
