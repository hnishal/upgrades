from scripts.helpful_scripts import encode_function_data, get_account, upgrade
from brownie import (
    Box,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    BoxV2,
    Contract,
    exceptions,
)
import pytest


def test_proxy_upgrades():
    account = get_account()
    box = Box.deploy({"from": account})
    proxy_admin = ProxyAdmin.deploy({"from": account})
    box_encoded_initializer_data = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        box.address,
        proxy_admin.address,
        box_encoded_initializer_data,
        {"from": account, "gas_limit": 1000000},
    )
    box_v2 = BoxV2.deploy({"from": account})
    proxy_box = Contract.from_abi("BoxV2", proxy.address, BoxV2.abi)
    with pytest.raises(exceptions.VirtualMachineError):
        proxy_box.increment({"from": account})

    tx = upgrade(account, proxy, box_v2.address, proxy_admin)
    tx.wait(1)
    proxy_box = Contract.from_abi("BoxV2", proxy.address, BoxV2.abi)
    assert proxy_box.retrieve() == 0
    proxy_box.increment({"from": account})
    assert proxy_box.retrieve() == 1
