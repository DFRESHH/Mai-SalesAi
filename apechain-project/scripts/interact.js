const hre = require("hardhat");

async function main() {
  // The address of your deployed contract
  const contractAddress = "0x9f93CD8DB9D48658D2cfC8aBBc4Edb8b5CdbaCe6";
  
  // Get the contract factory and attach it to the existing contract address
  const HelloApe = await hre.ethers.getContractFactory("HelloApe");
  const helloApe = await HelloApe.attach(contractAddress);
  
  // Read the current greeting
  const greeting = await helloApe.greeting();
  console.log("Current greeting:", greeting);
  
  // Set a new greeting
  console.log("Updating the greeting...");
  const tx = await helloApe.setGreeting("Hello from Hardhat!");
  await tx.wait(); // Wait for the transaction to be mined
  
  // Read the updated greeting
  const newGreeting = await helloApe.greeting();
  console.log("New greeting:", newGreeting);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
