import kin
from . import config
from .log import get as get_log
from .models import Payment, Wallet
from kin import AccountExistsError
from .utils import get_network_name
from .errors import ParseError
import stellar_base


kin_sdk = kin.SDK(
    secret_key=config.STELLAR_BASE_SEED,
    horizon_endpoint_uri=config.STELLAR_HORIZON_URL,
    network=get_network_name(config.STELLAR_NETWORK),
    channel_secret_keys=config.STELLAR_CHANNEL_SEEDS,
    kin_asset=stellar_base.asset.Asset(config.STELLAR_KIN_TOKEN_NAME,
                                       config.STELLAR_KIN_ISSUER_ADDRESS))
log = get_log()


def create_wallet(public_address: str, app_id: str) -> None:
    """create a wallet."""
    try:
        account_exists = kin_sdk.check_account_exists(public_address)
    except Exception as e:
        log.info('failed checking wallet state', public_address=public_address)
    else:
        if account_exists:
            raise AccountExistsError

    log.info('creating wallet', public_address=public_address)

    memo = '1-{}'.format(app_id)
    initial_xlm_amount = config.STELLAR_INITIAL_XLM_AMOUNT
    tx_id = kin_sdk.create_account(public_address, initial_xlm_amount, memo)
    log.info('create wallet transaction', tx_id=tx_id)
    return tx_id


def get_wallet(public_address: str) -> Wallet:
    data = kin_sdk.get_account_data(public_address)
    return Wallet.from_blockchain(data, kin_sdk.kin_asset)


def pay_to(public_address: str, amount: int, app_id: str, payment_id: str) -> Payment:
    """send kins to an address."""
    log.info('sending kin to', address=public_address)
    memo = Payment.create_memo(app_id, payment_id)
    tx_id = kin_sdk.send_kin(public_address, amount, memo_text=memo)
    return tx_id


def get_transaction_data(tx_id):
    data = kin_sdk.get_transaction_data(tx_id)
    return Payment.from_blockchain(data)


def try_parse_payment(tx_data):
    """try to parse payment from given tx_data. return None when failed."""
    try:
        return Payment.from_blockchain(tx_data)
    except ParseError as e:
        log.exception('failed to parse payment', tx_data=tx_data, error=e)
        return
    except Exception as e:
        log.exception('failed to parse payment', tx_data=tx_data, error=e)
        return
