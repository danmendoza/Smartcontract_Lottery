from brownie import Lottery, accounts, network, config, exceptions
from scripts.deploy_lottery import (
    deploy_lottery,
    start_lottery,
    enter_lottery,
    end_lottery,
    get_contract,
)
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2000 eth / usd (INITIAL_VALUE en helpful_scripts, en nuestro MockV3Aggregator establecemos el valor del ether a 2000$)
    # usdEntryFee is 50
    # 2000/1 == 50/x    x = 0.025
    expected_entrace_fee = Web3.toWei(0.025, "ether")
    entrace_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrace_fee == entrace_fee


def test_cant_enter_unless_starter():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter(
            {"from": get_account(), "value": lottery.getEntranceFee() + 100000000}
        )


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    fund_with_link(lottery.address)
    # Act
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 100000000})
    lottery.enter(
        {"from": get_account(index=1), "value": lottery.getEntranceFee() + 100000000}
    )
    lottery.enter(
        {"from": get_account(index=2), "value": lottery.getEntranceFee() + 100000000}
    )
    fund_with_link(lottery.address)
    balance_of_lottery = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"][
        "requestId"
    ]  # el fin de la loteria emite el evento que hemos creado
    vrf = get_contract("vrf_coordinator")
    STATIC_RNG = 777
    # 777 % 3 = 0, ganador = account
    starting_winner_balance = account.balance()
    vrf.callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == balance_of_lottery + starting_winner_balance
