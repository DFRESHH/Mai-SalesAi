# CLAUDE.md - Trading Bot Project Guidelines

## Commands
- Start the bot: `npm start`
- Compile contracts: `npx hardhat compile`
- Run tests: `npx hardhat test`
- Run specific test: `npx hardhat test test/Arbitrage.js`
- Deploy contract: `npx hardhat run scripts/deploy.js`
- Clean cache: `npx hardhat clean`

## Code Style Guidelines
- Use 2 space indentation
- Use camelCase for variables and functions
- Use PascalCase for contract names and classes
- Use async/await for promises, not .then()
- Always include error handling in try/catch blocks
- Validate inputs with require statements in Solidity
- Add comments for complex logic explaining the "why" not the "what"
- Use BigInt/Big.js for handling token amounts to prevent precision loss
- Import order: built-in modules, external packages, project modules
- Use const for variables that don't change

## Security Best Practices
- Never commit .env files or private keys
- Always check token balances before and after operations
- Implement ownership and access controls in contracts
- Always include a minimum output amount when swapping tokens