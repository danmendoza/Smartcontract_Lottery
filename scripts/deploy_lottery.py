from brownie import Lottery, network, config
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
import time


def deploy_lottery():
    account = get_account()
    feed = get_contract("eth_usd_price_feed").address
    vrfCoordinator = get_contract("vrf_coordinator").address
    link = get_contract("link_token").address
    keyhash = config["networks"][network.show_active()]["keyhash"]
    fee = config["networks"][network.show_active()]["fee"]

    # si la red no tiene definido el campo 'verify' devuelve False por defecto
    lottery = Lottery.deploy(
        feed,
        vrfCoordinator,
        link,
        fee,
        keyhash,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )

    print("Deployed lottery!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})  #
    starting_tx.wait(1)
    print("The lottery is started")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 1000000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(5)
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(5)
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(5)
    print("Entered in the Lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]

    # first we fund the contract with LINK
    # then end the lottery
    tx = fund_with_link(lottery.address)
    tx.wait(1)

    ending_transaction = lottery.endLottery(
        {"from": account}
    )  # esta funcion invocara la llamada a un nodo de la Chainlink, al que
    # tendremos que esperar a que nos responda
    ending_transaction.wait(1)

    time.sleep(60)
    print(f"{lottery.recentWinner()} is the new WINNER!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()

