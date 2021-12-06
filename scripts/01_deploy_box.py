from brownie import (
    network,
    Box,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    Contract,
    BoxV2,
    config,
)
from scripts.helpful_scripts import get_account, encode_function_data, upgrade


def main():
    account = get_account()
    print(f"Deploying to {network.show_active()}")
    box = Box.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    print(f"box deployed at {box.address}")
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    # initializer for our box contract
    # we have to encode our initializer to bytes as the constructor of TUP.sol
    # takes byte data(byte form of out initializer) and send it for upgrade and call
    # initializer = box.store, 1
    # not using for now
    print(f"ProxyAdmin deployed at {proxy_admin.address}")
    box_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        box.address,
        proxy_admin.address,
        box_encoded_initializer_function,
        {"from": account, "gas_limit": 1000000},
        # publish_source=config["networks"][network.show_active()]["verify"]
        # added gas limit to be safe sometimes proxy have hasrd time figuring out gas
    )
    print(f"Proxy deployed to {proxy}, you can now upgrade to v2!")
    proxy_box = Contract.from_abi("Box", proxy.address, Box.abi)
    # being a proxy it will delegate all funciton to implentaton(box) contract
    proxy_box.store(1, {"from": account})
    print(f"New Value : {proxy_box.retrieve()}")

    # upgrading to box_v2
    # 1. Deploying BoxV2
    box_v2 = BoxV2.deploy(
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    # 2. upgrading the implementatino
    upgrade_transaction = upgrade(account, proxy, box_v2.address, proxy_admin)
    upgrade_transaction.wait(1)
    print("proxy has been upgraded!")
    # 3. creating on object of proxy which delegates to boxv2
    proxy_box = Contract.from_abi("BoxV2", proxy.address, BoxV2.abi)
    print(f"Starting value {proxy_box.retrieve()}")
    # this will return 1 as variables are stored on proxy contract instead of implementaion
    tx_incr = proxy_box.increment({"from": account})
    tx_incr.wait(1)
    print(f"New Value from BoxV2: {proxy_box.retrieve()}")
