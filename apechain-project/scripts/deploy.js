const hre = require("hardhat");

async function main() {
  const HelloApe = await hre.ethers.getContractFactory("HelloApe");
  console.log("Deploying HelloApe...");
  
  const helloApe = await HelloApe.deploy();
  
  // Wait for the transaction to be mined
  console.log("Deployment transaction:", helloApe.deploymentTransaction().hash);
  
  await helloApe.waitForDeployment();
  
  console.log("HelloApe deployed to:", await helloApe.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});