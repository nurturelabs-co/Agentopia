from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_KEY: str = ""
    USER_PRIVATE_KEY: str = ""
    CHAIN_EXPLORER: str = "https://basescan.org/"
    PRODUCT_FUN_API: str = "https://api.agentopia.xyz"
    RPC: str = "https://mainnet.base.org"
    GAS_PRICE: int = int(0.1e9)
    CHAIN_ID: int = 8453
    MICROPAYMENT_ADDRESS: str = "0xaEF2fc1f54AE5b260cA2123B27bE6E79C3AAFa7a"
    USDC_ADDRESS: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    AGENTOPIA_LOCAL_MODEL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()
