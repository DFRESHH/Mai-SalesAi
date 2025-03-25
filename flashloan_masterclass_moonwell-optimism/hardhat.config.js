require("dotenv").config()
require("@nomicfoundation/hardhat-toolbox")

const privateKey = process.env.PRIVATE_KEY || ""

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.18",
  networks: {
    hardhat: {
      forking: {
        url: `https://opt-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
        blockNumber: process.env.FORK_BLOCK_NUMBER === "true" ? 131285000 : undefined
      },
    }
  }
};
