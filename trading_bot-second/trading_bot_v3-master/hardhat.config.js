require("dotenv").config(); // Load environment variables

module.exports = {
  solidity: "0.8.18", // Specify the Solidity version
  networks: {
    hardhat: {
      chainId: 31338, // Unique chain ID for the second bot
      forking: {
        url: `https://arb-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
      },
    },
    localhost: {
      url: "http://127.0.0.1:8555", // Second bot runs on port 8555
    },
  },
};