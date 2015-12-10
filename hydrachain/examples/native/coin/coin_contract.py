import hydrachain.native_contracts as nc
from ethereum import utils
import ethereum.slogging as slogging
log = slogging.get_logger('ifs.contracts')


DEBUG = utils.DEBUG

STATUS = 'uint16'
FORBIDDEN = 403
NOTFOUND = 404
OK = 200
ERROR = 500
BADREQEST = 400
INSUFFICIENTFUNDS = PAYMENTREQUIRED = 402


def isaddress(x):
    return len(x) == 20 and x != '\0' * 20


class CoinSent(nc.ABIEvent):
    args = [dict(name='from', type='address', indexed=True),
            dict(name='value', type='uint256', indexed=True),
            dict(name='to', type='address', indexed=True)]


class Coin(nc.NativeContract):
    address = utils.int_to_addr(5001)
    events = [CoinSent]

    owner = nc.Scalar('address')
    holdings = nc.Dict('uint32')
    holders = nc.List('address')

    # FIXME: call only once, call on init
    def init(ctx, returns=STATUS):
        log.DEV('In Coin.init')
        if isaddress(ctx.owner):
            return FORBIDDEN
        ctx.owner = ctx.tx_origin
        ctx.holders.append(ctx.tx_origin)
        ctx.holdings[ctx.tx_origin] = 1000000
        return OK

    def sendCoin(ctx, _value='uint32', _to='address', returns=STATUS):
        if ctx.holdings[ctx.msg_sender] >= _value:
            if not ctx.holdings[_to]:
                ctx.holders.append(_to)
            ctx.holdings[ctx.msg_sender] -= _value
            ctx.holdings[_to] += _value
            ctx.CoinSent(ctx.msg_sender, _value, _to)
            return OK
        else:
            raise RuntimeError()

    @nc.constant
    def creator(ctx, returns='address'):
        return ctx.owner

    @nc.constant
    def coinBalance(ctx, returns='uint32'):
        return ctx.holdings[ctx.msg_sender]

    @nc.constant
    def coinBalanceOf(ctx, _holder='address', returns='uint32'):
        return ctx.holdings[_holder]

    @nc.constant
    def num_holders(ctx, returns='uint32'):
        return len(ctx.holders)

    # FIXME: protect owner or company_address
    @nc.constant
    def get_holders(ctx, returns='address[]'):
        return list(ctx.holders)


# register contracts
nc.registry.register(Coin)


def get_abi():
    abi = []
    for c in nc.registry.abi_contracts():
        abi.append({c.__name__: dict(abi=c.json_abi(), template_address=c.address.encode('hex'))})
    return abi

if __name__ == '__main__':
    import json
    print json.dumps(get_abi())
    print 'generating contract',
