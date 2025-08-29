import os
from typing import Sequence
from google import genai
from google.genai.types import Part, HttpOptions
from google.oauth2.credentials import Credentials
from google.auth.transport import Request
from google.genai import Client

# from genai_common.proxy_token_roller import coin_proxy_token_roller, ProxyTokenRoller

# os.environ["SSL_CERT_FILE"] = (
#     "reg_interpret_transform/resources/certs/CitiInternalCAChain_PROD.pem"
# )

# os.environ["REQUESTS_CA_BUNDLE"] = (
#     "reg_interpret_transform/resources/certs/CitiInternalCAChain_PROD.pem"
# )

# os.environ["COIN_CERT_FILE"] = (
#     "reg_interpret_transform/resources/certs/CitiInternalCAChain_UAT.pem"
# )

# token_roller: ProxyTokenRoller = coin_proxy_token_roller(
#     url="https://uat-coin-nam.msrpnt.net/as/token.oauth2",
#     client_id=os.environ.get("COIN_CLIENT_ID", ""),
#     client_secret=os.environ.get("COIN_CLIENT_SECRET", ""),
#     scope="baseSaas-6c52-4dce-bd57-71ca19c63d12",
#     ssl_cert_file=os.environ.get("COIN_CERT_FILE"),
# )


# def get_coin_token(request: Request, scopes: Sequence[str]):
#     token, expiry = token_roller.get_token_and_expiry(flush_cache=True)
#     return token, expiry.replace(tzinfo=None)


try:
    client: Client | None = None
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        print("AI client initialized successfully")
    else:
        client = None
        print("Warning: GEMINI_API_KEY not found. AI features will be disabled.")
except Exception as e:
    client = None
    print(
        f"Warning: Failed to initialize AI client: {e}. AI features will be disabled."
    )

MODEL = "gemini-2.5-flash"
