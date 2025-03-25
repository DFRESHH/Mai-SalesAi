require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.28",
  networks: {
    curtis: {
      url: "https://curtis.rpc.caldera.xyz/http",
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};