# Chainlink Hackathon Backend
## Introduction
This backend serves API that gets consumed by script running at Chainlink's DON (Decentralized Oracle Network)

## Algorithm
1. Stability Pool Share Size</br>
Stability Pool size in $ / $mkUSD outstanding supply = SP share size. The stability pool size can be found from [here](https://api.prismamonitor.com/v1/mkusd/ethereum/holders) and circulating supply can be queried from the [smart contract](https://etherscan.io/token/0x4591dbff62656e7859afe5e45f6f47d3669fbb28#readContract) itself

2. Calculate average of price impact from API. For example this link: https://api.prismamonitor.com/v1/collateral/ethereum/0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0/impact

3. 