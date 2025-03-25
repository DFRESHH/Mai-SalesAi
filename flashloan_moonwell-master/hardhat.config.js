require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";
const FORK_BLOCK_NUMBER = process.env.FORK_BLOCK_NUMBER ? parseInt(process.env.FORK_BLOCK_NUMBER) : undefined;

if (!ALCHEMY_API_KEY) {
  console.error("❌ ERROR: Missing ALCHEMY_API_KEY in .env");
  process.exit(1);
}

module.exports = {
  solidity: "0.8.18",
  networks: {
    hardhat: {
      forking: {
        url: `https://base-mainnet.blastapi.io`,
        blockNumber: FORK_BLOCK_NUMBER || 18343040,
      },
    },
    base: {
      url: "https://mainnet.base.org",
      accounts: [PRIVATE_KEY],
      chainId: 8453,
      gasPrice: "auto"
    }
  },
};