// -- HANDLE INITIAL SETUP -- //
require("dotenv").config();
require("./helpers/server");

const Big = require("big.js");
const ethers = require("ethers");
const config = require("./config.json");
const { getTokenAndContract, getPoolContract, getPoolLiquidity, calculatePrice } = require("./helpers/helpers");
const { provider, uniswap, pancakeswap, arbitrage } = require("./helpers/initialization");

// -- CONFIGURATION VALUES -- //
const ARB_FOR = config.TOKENS.ARB_FOR;
const ARB_AGAINST = config.TOKENS.ARB_AGAINST;
const POOL_FEE = config.TOKENS.POOL_FEE;
const UNITS = config.PROJECT_SETTINGS.PRICE_UNITS;
const PRICE_DIFFERENCE = config.PROJECT_SETTINGS.PRICE_DIFFERENCE;
const GAS_LIMIT = config.PROJECT_SETTINGS.GAS_LIMIT;
const GAS_PRICE = config.PROJECT_SETTINGS.GAS_PRICE;

let isExecuting = false;

const main = async () => {
  const { token0, token1 } = await getTokenAndContract(ARB_FOR, ARB_AGAINST, provider);
  const uPool = await getPoolContract(uniswap, token0.address, token1.address, POOL_FEE, provider);
  const pPool = await getPoolContract(pancakeswap, token0.address, token1.address, POOL_FEE, provider);

  console.log(`Using ${token1.symbol}/${token0.symbol}\n`);
  console.log(`Uniswap Pool Address: ${await uPool.getAddress()}`);
  console.log(`Pancakeswap Pool Address: ${await pPool.getAddress()}\n`);

  uPool.on("Swap", () => eventHandler(uPool, pPool, token0, token1));
  pPool.on("Swap", () => eventHandler(uPool, pPool, token0, token1));

  console.log("Waiting for swap event...\n");
};

const eventHandler = async (_uPool, _pPool, _token0, _token1) => {
  if (!isExecuting) {
    isExecuting = true;
    const priceDifference = await checkPrice([_uPool, _pPool], _token0, _token1);
    const exchangePath = await determineDirection(priceDifference);

    if (!exchangePath) {
      console.log(`No Arbitrage Currently Available\n`);
      isExecuting = false;
      return;
    }

    const { isProfitable, amount } = await determineProfitability(exchangePath, _token0, _token1);

    if (!isProfitable) {
      console.log(`No Profitable Trade Available\n`);
      isExecuting = false;
      return;
    }

    await executeTrade(exchangePath, _token0, _token1, amount);
    isExecuting = false;
    console.log("\nWaiting for swap event...\n");
  }
};

const determineDirection = async (_priceDifference) => {
  console.log(`Determining Direction...\n`);

  if (_priceDifference >= PRICE_DIFFERENCE) {
    console.log(`Potential Arbitrage Direction:\n`);
    console.log(`Buy     -->     Uniswap V3`);
    console.log(`Sell    -->     Pancakeswap V3\n`);
    return [uniswap, pancakeswap];
  }

  return null;
};

const executeTrade = async (_exchangePath, _token0, _token1, _amount) => {
  console.log(`Attempting Arbitrage: Buying on Uniswap and Selling on PancakeSwap\n`);

  const routerPath = [
    await _exchangePath[0].router.getAddress(),
    await _exchangePath[1].router.getAddress()
  ];

  const tokenPath = [
    _token0.address,
    _token1.address
  ];

  const account = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
  const tokenBalanceBefore = await _token0.contract.balanceOf(account.address);
  const ethBalanceBefore = await provider.getBalance(account.address);

  if (config.PROJECT_SETTINGS.isDeployed) {
    const transaction = await arbitrage.connect(account).executeTrade(
      routerPath,
      tokenPath,
      POOL_FEE,
      _amount
    );

    await transaction.wait(0);
  }

  const tokenBalanceAfter = await _token0.contract.balanceOf(account.address);
  const ethBalanceAfter = await provider.getBalance(account.address);

  console.table({
    'ETH Balance Before': ethers.formatUnits(ethBalanceBefore, 18),
    'ETH Balance After': ethers.formatUnits(ethBalanceAfter, 18),
    'ETH Spent (gas)': ethers.formatUnits((ethBalanceBefore - ethBalanceAfter).toString(), 18),
    'WETH Balance BEFORE': ethers.formatUnits(tokenBalanceBefore, _token0.decimals),
    'WETH Balance AFTER': ethers.formatUnits(tokenBalanceAfter, _token0.decimals),
    'WETH Gained/Lost': ethers.formatUnits((tokenBalanceAfter - tokenBalanceBefore).toString(), _token0.decimals)
  });
};

main();
