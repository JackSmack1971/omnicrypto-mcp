# Free Crypto Data Ingestion for AI Agents — Deduplicated Master List

*Consolidated from three overlapping research passes (checked as of Oct 2026). Duplicate entries merged; conflicting figures noted where sources disagreed.*

---

## 1. MCP Servers — Hosted / Remote (Zero-Config)

| Service | Endpoint | Auth | Key Features |
|---|---|---|---|
| **CoinGecko MCP** | `https://mcp.api.coingecko.com/mcp` (also `/sse`) | No key | 76+ tools, 1M+ assets, prices, OHLCV, DeFi pools, NFTs, exchanges, trending. Keyless, shared rate limit (~27 calls/min to free tier) |
| **CoinMarketCap MCP** | `https://mcp.coinmarketcap.com/mcp` | Free Basic key (30 calls/min, 10–15K credits/mo) | 12 tools, 10K+ cryptos, TA, on-chain metrics, global overview, trending narratives |
| **CoinMarketCap MCP (x402)** | `https://mcp.coinmarketcap.com/x402/mcp` | No key — pay-per-call USDC | Not actually free (0.01 USDC/call) |
| **Bitquery MCP** | `https://mcp.bitquery.io` | OAuth 2.1 (free account) | DEX trades, transfers, OHLC candles, wallet history, AML/KYC, forensics across 8–9 chains |
| **CoinPaprika MCP** | `https://mcp.coinpaprika.com/sse` or `/streamable-http` | No key | 31 tools: coins, tickers, OHLCV, exchanges, search, converter (~20K calls/mo) |
| **DexPaprika MCP** | `npx dexpaprika-mcp` or `https://mcp.dexpaprika.com/streamable-http` | No key (free key optional) | 18+ tools: pools, tokens, trades, OHLCV, 20–36 networks |
| **Tickscope MCP** | `uvx tickscope-mcp` | No key | Real-time WebSocket data, 73 technical indicators, chart patterns, multi-exchange (Binance, Bybit, OKX) |
| **Bitcoin MCP (JamesANZ)** | `npx @jamesanz/bitcoin-mcp` | No key | Bitcoin addresses, transactions, blocks, UTXOs via mempool.space |
| **Bitcoin MCP (AbdelStark)** | `npx -y bitcoin-mcp@latest` | No key | Key generation, address validation, tx decoding, Lightning Network, LNBits |
| **ChainRPC MCP** | `https://chainrpc-mcp.mitander.io/mcp` or `npx -y chainrpc-mcp` | No key | EVM + Bitcoin RPC: balances, blocks, txs, logs, contract reads, gas estimation |
| **Alchemy MCP** | hosted + CLI | Free tier (30M CUs/mo, 15 req/s) | 159+ tools across token/NFT/tx data, 100+ chains, wallet-based signup |
| **Blockscout MCP** | `npx karacurt/blockscout-mcp-server` | No key | Balances, tokens, NFTs via Blockscout explorer instances |
| **CoinStats MCP** | `npx CoinStatsHQ/coinstats-mcp` | Free tier (20K credits/mo) | Market data, portfolio tracking, news, wallets, token security |
| **DexScreener MCP** | `opensvm/dexscreener-mcp-server`, `kukapay/dexscreener-trending-mcp` | No key | DEX pairs, trending tokens across 80+ chains |
| **Hive Intelligence MCP** | `hiveintelligence.xyz/mcp` / npm package | No key for basic | Market data, DeFi, wallets, token risk, DEX flows, NFTs across 50+ chains |
| **Abstraxn Public Web3 MCP** | hosted | No key | Block numbers, tx status, gas info, ERC-20 info, spot prices, unsigned tx builder (EVM + Solana) |
| **CoinCap MCP** | `QuantGeekDev/coincap-mcp` | No key | Real-time market data |
| **Dune Analytics MCP** | `docs.dune.com/api-reference/agents/mcp` | ⚠️ Free plan is view-only; paid Analyst plan needed for execution | SQL analytics on indexed chains |
| **Pyth MCP** | `Chop-Kampfire/pyth-mcp-server`, `itsOmSarraf/pyth-network-mcp` | No key | Oracle price feeds, candles, TWAP (1,900+ feeds) |
| **crypto-feargreed MCP** | `kukapay/crypto-feargreed-mcp` | No key | Fear & Greed Index, real-time + historical |
| **free-crypto-news MCP** | `cryptocurrency.cv` / self-hosted | No key | 130–200+ news sources, 662K+ historical articles, sentiment, RSS, SSE, 42 languages |
| **The Graph MCP / Token API MCP** | `Data-Nexus-Web3/thegraph-mcp` | Free tier | Subgraph search, GraphQL queries, token metadata/balances/holders |
| **Birdeye MCP** | hosted | Free tier (30K CU/mo) | Solana/EVM token discovery, OHLCV, liquidity, wallet PnL |
| **Chainbase MCP** | hosted | Free tier (200K credits/mo) | 90+ chains, REST + SQL |
| **Moralis (Cortex) MCP** | hosted | Free tier | Wallet/token/NFT data, streams |
| **Helius MCP** | hosted | Free tier (1M credits/mo) | Solana RPC + DAS + enhanced APIs, webhooks |
| **Tatum Blockchain MCP** | `tatumio/blockchain-mcp` | Free key (3 req/s, 100K lifetime credits) | 130+ networks via unified Data API/RPC |
| **GetBlock / QuickNode / Chainstack MCPs** | hosted | Free tiers | Multi-chain RPC |
| **Glassnode MCP** | hosted | Free community metrics | On-chain metrics |
| **CryptoQuant MCP** | hosted | Free basic | Exchange flows, MVRV, funding |
| **OKX OnchainOS Skills/MCP** | hosted | Free with limits | 20+ chains |
| **Crypto.com Market Data MCP** | hosted | No key | Live prices, volumes, trends |
| **Maestro MCP** | hosted | — | Bitcoin blocks, mempool, wallets |
| **Santiment MCP** | `https://api.santiment.net/mcp` | OAuth 2.0, free tier | On-chain + social metrics, asset timeseries |
| **Polymarket MCP** | `npx -y @quantish/polymarket-server` or `@polyrama/mcp` | No key | Prediction markets: discovery, orders, positions |
| **Kalshi MCP** | `npx -y @quantish/kalshi-server` | No key | 40 tools for Kalshi prediction markets |
| **RootData MCP** | `npx nvmmonkey/Rootdata-MCP` | No key | Crypto asset data, market trends, ecosystem mapping |
| **Octav MCP** | `npx Octav-Labs/octav-api-mcp` | No key / free tier | Portfolio tracking, tx history, DeFi analytics across 20+ chains |
| **FinanceKit MCP** | `npx vdalhambra/financekit-mcp` | No key | 17 tools: stocks, crypto (CoinGecko), TA, risk metrics, options, portfolio |
| **Sharpe MCP** | `uvx sharpe-mcp` | No key | Derivatives, funding, arbitrage, narratives, news, token risk |
| **Funding Rates MCP** | `npx kukapay/funding-rates-mcp` | No key | Real-time funding rates across exchanges |
| **Crypto News MCP** | `npx kukapay/crypto-news-mcp` | Free NewsData key | Real-time crypto news, headlines, search |
| **Crypto Trending MCP** | `npx kukapay/crypto-trending-mcp` | No key | Trending tokens on CoinGecko |
| **ETF Flow MCP** | `npx kukapay/etf-flow-mcp` | No key | Crypto ETF flow data |
| **Crypto Portfolio MCP** | `npx kukapay/crypto-portfolio-mcp` | No key | Portfolio management, optimization |
| **Token Revoke MCP** | `npx kukapay/token-revoke-mcp` | No key | Manage/revoke ERC-20 allowances |
| **Real-time Crypto MCP (CoinCap-based)** | `npx smhnkmr/realtime-crypto-mcp-server` | No key | Real-time crypto data via CoinCap |
| **Jupiter MCP (Solana)** | `npx quanghuynguyen1902/jupiter-mcp-server` or `alansory/cursor-talk-to-jupiter-mcp` | No key | Solana DEX swaps, price quotes |
| **Multichain MCP (wkalidev)** | `npx @wkalidev/multichain-mcp` | No key | Stacks, Celo, Base: balances, prices, transfers |
| **DeFi MCP (matiosera3-ops)** | self-host | No key | Aave v3 positions, Chainlink prices, Uniswap v3 simulation |
| **DeBridge MCP / Relay Protocol MCP** | self-host / `npm i -g @relayprotocol/relay-mcp` | No key | Cross-chain swap routes, fees, bridge tracking |
| **Chain.Love MCP** | hosted | No key | Web3 infra discovery: RPCs, indexing, oracles across 50+ networks |
| **OpenChainBench MCP** | `https://openchainbench.com/api/mcp/mcp` | No key | Live RPC latency across 22 EVM chains + Solana, oracle deviation, bridge fees |
| **EVM MCP Server (mcpdotdirect / sinco-lab / karacurt / qingfengzxr etc.)** | various | No key (public RPCs) | 30+ EVM chains: balances, tokens, NFTs, ENS, contracts |
| **CCXT MCP** | `npx @lazy-dinosaur/ccxt-mcp`, `pcriadoperez/ccxt-mcp`, `doggybee/mcp-server-ccxt` | No key for public data | 100+ exchanges via CCXT, OHLCV, order books, tickers |
| **Binance MCP** | `npx berlinbra/binance-mcp`, `snjyor/binance-mcp`, others | No key for market data | Binance market data, prices, klines |
| **Etherscan MCP** | `npx haomingdev/etherscan-mcp`, `huahuayu/etherscan-mcp-server`, `crazyrabbitLTC/mcp-etherscan-server` | Free Etherscan key | Multi-chain Etherscan data: addresses, txs, tokens, gas |
| **Solscan MCP** | `npx wowinter13/solscan-mcp`, `bobtista/solscan_mcp_server` | Solscan API (free tier / Pro) | Solana blockchain data |
| **Universal / multi-chain MCPs** | `GOAT` (goat-sdk/goat), `strangelove-ventures/web3-mcp`, `nirholas/universal-crypto-mcp` | Open source | 20–380+ tools across many chains |
| **Solana Agent Kit** | `sendaifun/solana-agent-kit` | Open source | 40+ Solana actions |

---

## 2. MCP Servers — Self-Hosted / Open Source (Domain-Specific, GitHub)

Deduplicated catalog of the `kukapay/*` and related suites (each a separate repo, all free/OSS):

- **DeFi/yield**: `dcSpark/mcp-server-defillama`, `kukapay/defi-yields-mcp`, `kukapay/aave-mcp`, `kukapay/euler-vaults-mcp`, `Philidor-Labs/philidor-mcp`
- **Market/oracle/indicators**: `kukapay/chainlink-feeds-mcp`, `kukapay/crypto-indicators-mcp`, `kukapay/crypto-orderbook-mcp`, `kukapay/crypto-liquidations-mcp`
- **Ethereum/EVM**: `kukapay/ens-mcp`, `kukapay/contract-scraper-mcp`, `kukapay/findblock-mcp`, `kukapay/ethereum-validators-queue-mcp`
- **Solana**: `kukapay/jupiter-mcp`, `kukapay/raydium-launchlab-mcp`, `kukapay/pumpfun-wallets-mcp`, `kukapay/memecoin-radar-mcp`, `kukapay/solana-launchpads-mcp`, `solana-foundation/solana-dev-mcp`, `Aldrin-labs/solana-mcp-server`, `N-45div/SolMCP`
- **Whale/on-chain activity**: `kukapay/whale-tracker-mcp`, `kukapay/wallet-inspector-mcp`, `kukapay/tornado-cash-mcp`, `kukapay/hyperliquid-whalealert-mcp`
- **Security**: `kukapay/honeypot-detector-mcp`, `kukapay/rug-check-mcp`, `mohitparmar1/Solana-Wallet-Security-Scanner` (token-revoke-mcp listed above)
- **Bridges**: `debridge-finance/debridge-mcp`, `kukapay/bridge-rates-mcp`, `kukapay/bridge-metrics-mcp`, `kukapay/wormhole-metrics-mcp`, `kukapay/stargate-bridge-mcp`
- **News/sentiment**: `kukapay/cryptopanic-mcp-server`, `kukapay/cointelegraph-mcp`, `kukapay/blockbeats-mcp`, `kukapay/crypto-rss-mcp`, `kukapay/crypto-whitepapers-mcp`, `kukapay/crypto-sentiment-mcp` (mcp-crypto-sentiment / gravison-group)
- **Prediction markets**: `kukapay/polymarket-predictions-mcp`
- **NFT**: `ProjectOpenSea/opensea-skill`, `Tairon-ai/magiceden-mcp`, `kukapay/nft-analytics-mcp`
- **CEX (market data keyless; trading needs keys)**: `bybit-exchange/bybit-mcp`, `bybit-exchange/trading-mcp`, `nirholas/binance-mcp`, `dlwjdtn535/mcp-bybit-server`, `sydowma/crypto_exchange_mcp`
- **Bitcoin**: `AbdelStark/bitcoin-mcp`, `kukapay/bitcoin-utxo-mcp`, `AbdelStark/lightning-mcp`
- **Infra management**: `quiknode-labs/qn-mcp`, Chainstack MCP, `noditlabs/nodit-mcp-server`, `moralisweb3/moralis-mcp-server`, `thirdweb-dev/ai`
- **Other chains**: `Outblock/flow-mcp` (Flow), `gluneau/near-mcp-server` (NEAR), `kriuchkov/ton-mcp` (TON), `adairrr/cosmwasm-mcp` (CosmWasm), `b-open-io/bsv-mcp` (Bitcoin SV), `ordiscan/ordiscan-mcp` (Ordinals/Runes), `Sifu213/monad-mcp-magiceden` (Monad), `MCPxLabs/mcpsol` / `Rayato159/sol-chad-mcp` (Solana wallets)
- **Misc**: `getnimbus/spice` (Flipside/Solana SQL runtime), `tumf/web3-mcp` (Ankr), `albertma/blockchain-mcp` (ETH + VeChain), `rjn32s/mcp-blockchain`, `HARISHSENTHIL/web3_mcp`, `mark3labs/phalcon-mcp` (BlockSec Phalcon), `joaquim-verges/blockchain-mcp` (thirdweb), `blackfrogai/crypto-mcp`, `0xanpham/my-crypto-mcp`, `Hott-J/coingecko-mcp-server`, `riteshyaaa/MCP-BTC-Watch`, `friendlygeorge/coingecko-mcp-server`, `QuantGeekDev/coincap-mcp`, `alchemyplatform/alchemy-mcp`, `Blockchain-MCPs/coingecko-mcp`

**Directories for ongoing discovery**: `hive-intel/awesome-crypto-mcp-servers`, `KyleMillion/awesome-crypto-mcp`, `badkk/awesome-crypto-mcp-servers`, `buddies2705/awesome-crypto-mcp`, `sendaifun/awesome-solana-mcp-servers`, `kukapay/kukapay-mcp-servers`, `royyannick/awesome-blockchain-mcps`, `demcp/awesome-web3-mcp-servers`, `TensorBlock/awesome-mcp-servers`; registries: Smithery, Glama AI, MCPHub, mcp.so, official `modelcontextprotocol/servers`, PulseMCP.

---

## 3. Keyless REST / WebSocket APIs (No Signup)

| Service | Base URL | Data | Limits |
|---|---|---|---|
| **CoinGecko Keyless Public API** | `api.coingecko.com/api/v3` | Prices, market cap, volume, metadata, categories, exchanges, trending, global stats, 1M+ assets | ~10–30 req/min shared IP pool |
| **DexScreener** | `api.dexscreener.com` | Pairs across 80+ chains, prices, volume, liquidity, txns, profiles, boosts | 300 req/min (pairs/tokens), 60 req/min (profiles/boosts) |
| **DefiLlama** (+ Coins, Stablecoins, Yields sub-APIs) | `api.llama.fi`, `coins.llama.fi`, `stablecoins.llama.fi`, `yields.llama.fi` | TVL, protocols, stablecoins, yields/APY, DEX volumes, fees, revenue, open interest, token prices by contract | No auth, standard rate limit; has `llms-free.txt` |
| **GeckoTerminal** | `api.geckoterminal.com/api/v2` | On-chain DEX pools, tokens, OHLCV, trades across 200+ networks, 1,500+ DEXes | ~10–30 calls/min keyless |
| **CoinMarketCap Keyless Public API** | `pro-api.coinmarketcap.com/public-api` | Listings, quotes, metadata, global metrics, Fear & Greed, DEX pairs/holders, K-line data (35–63 endpoints) | IP-based shared pool |
| **CoinPaprika API** | `api.coinpaprika.com/v1` | 12K+ coins, tickers, exchanges, OHLCV, search, market pairs | ~20–25K calls/mo equivalent |
| **CoinCap API** | `api.coincap.io/v2` (note: v2 retired; moved to keyed `rest.coincap.io/v3`) | Prices, market cap, volume, exchanges, assets | Free (v2 legacy) / free key (v3) |
| **CoinLore API** | `api.coinlore.net` | 10K+ coins, tickers, global market data, exchanges | Fully keyless, low rate limit |
| **DexPaprika API** | `api.dexpaprika.com` | DEX pools, tokens, trades, OHLCV across 20–36 networks | Keyless 15–50K req/credits/mo; free key 30K–300K/mo |
| **Hyperliquid Info API** | `api.hyperliquid.xyz/info` | Perp + spot mids, order books, candles, market/meta, user state | POST-based, no key |
| **dYdX Indexer** | — | Perps markets, funding, trades | Keyless |
| **Jupiter API** | `quote-api.jup.ag` / `lite-api.jup.ag` | Solana DEX quotes, swap routes, token lists, prices | No key |
| **0x API** | — | EVM swap quotes, price, liquidity sources | Free tier (key recommended) |
| **1inch API** | `rpc.1inch.io` | EVM aggregation quotes/routes, spot prices | Free dev-portal key |
| **KyberSwap / Odos / OpenOcean / ParaSwap (Velora) APIs** | various | DEX aggregation quotes | Free |
| **Uniswap subgraphs / The Graph** | — | Pools, swaps, ticks, volume | Free rate-limited (Studio/API key) |
| **alternative.me Fear & Greed** | `api.alternative.me/fng/` | Current + historical Crypto Fear & Greed Index | Free forever, ~60 req/10min, commercial use OK |
| **mempool.space API** | `mempool.space/api` | Bitcoin mempool, blocks, fees, addresses, txs, WebSocket | Free, no key, self-hostable |
| **Blockstream Esplora** | `blockstream.info/api` | Bitcoin/Liquid block explorer data | Keyless |
| **Blockchain.com / Blockchain.info API** | `blockchain.info` / `blockchain.com` | BTC blocks, txs, addresses, charts, WebSocket | Free, keyless, rate-limited |
| **Ethplorer** | `api.ethplorer.io` | Ethereum token info, holders, txs | Keyless with limits; free key raises them |
| **Blockscout instances** | e.g. `eth.blockscout.com/api` | Etherscan-style multi-chain data | Keyless (Pro API increasingly keyed) |
| **GoPlus Security** | `api.gopluslabs.io` | Token security/honeypot/rug heuristics, dApp security | Keyless core endpoints |
| **Honeypot.is** | — | Honeypot + tax simulation for tokens | Keyless |
| **RugCheck** | `api.rugcheck.xyz` | Solana token risk reports | Keyless |
| **Pyth Hermes (+ Benchmarks)** | `hermes.pyth.network` | Real-time + historical oracle prices, 1,900+ feeds | Keyless |
| **Chainlink Data Feeds** | on-chain | Decentralized reference price feeds | Free to read via RPC |
| **Polymarket (Gamma + Data + CLOB APIs)** | `gamma-api.polymarket.com`, `data-api.polymarket.com` | Prediction-market prices, order books, resolution, positions | Public, no key |
| **Snapshot** | `demo.snapshot.box` / governance APIs | DAO proposals & votes | Keyless |
| **Whale Alert `/status`** | — | Supported chains/symbols list only (tx API is paid) | Keyless |
| **L2Beat / growthepie / Ultrasound.money** | — | L2 TVL/stages/activity, L2 fundamentals, ETH supply/burn | Keyless |
| **LI.FI / deBridge APIs** | — | Cross-chain quotes, routes, tx building | Free reads |
| **Sourcify / 4byte / OpenChain** | — | Verified contract source/metadata, function signature DBs | Keyless |
| **Bitnodes** | — | Bitcoin network node census | Keyless |
| **MEV-Boost Relay Data API / Flashbots Protect RPC** | `rpc.flashbots.net` | Relay bids/payloads; MEV-protected RPC | Keyless |
| **CryptoPanic RSS / Cointelegraph / CoinDesk / Decrypt / The Block RSS** | — | News headline ingestion | Free RSS/Atom (CryptoPanic JSON API now paid — RSS remains free) |
| **XOOMAR Sentiment API** | `xoomar.com/api/markets/sentiment` | Sentiment for 26 assets (crypto, equities, FX, indices, commodities) | 10 req/min keyless, 30 with free key |
| **Agents Gate Sentiment** | `positivesearch.app/api/v35/` | News sentiment index for BTC, Gold, Oil | Open, no key |
| **three.ws Crypto API / Aggregated API** | `three.ws/api/*` | Market snapshot, rug check, holder spread, whale flow, DEX pairs, swap quotes (Solana & Base) | Keyless |
| **CoinGecko Token Lists** | `tokens.coingecko.com/{chain}/all.json` | Token lists per chain | No key |

---

## 4. Centralized Exchange Public Market Data (No Key for Reads)

| Exchange | REST Base | WebSocket |
|---|---|---|
| **Binance** (spot + USDT-M futures) | `api.binance.com/api/v3`, `fapi.binance.com` | `wss://stream.binance.com:9443/ws` |
| **Coinbase Exchange** | `api.exchange.coinbase.com` | `wss://ws-feed.exchange.coinbase.com` (unauthenticated) |
| **Kraken** | `api.kraken.com/0/public` | `wss://ws.kraken.com/v2` |
| **KuCoin** | `api.kucoin.com` | `wss://ws-api.kucoin.com` |
| **Bybit** | `api.bybit.com/v5/market` | `wss://stream.bybit.com` |
| **OKX** | `www.okx.com/api/v5/market` | `wss://ws.okx.com:8443` |
| **Bitget** | `api.bitget.com/api/v2` | Public WS available |
| **Gate.io** | `api.gateio.ws/api/v4` | Public WS available |
| **MEXC** | `api.mexc.com/api/v3` | Public WS |
| **Bitfinex** | `api-pub.bitfinex.com/v2` | Public WS |
| **Crypto.com** | `api.crypto.com/exchange/v1/public` | Public WS |
| **Deribit** | `www.deribit.com/api/v2/public` | Options/futures tickers, funding, open interest |
| **Hyperliquid** | `api.hyperliquid.xyz` | Perpetuals market data, order books, funding |
| **HTX, Gemini, Upbit** | public endpoints | Keyless market data (verify ToS for redistribution) |

**Tip:** wrap all of these with the open-source **CCXT** library instead of hand-rolling clients.

---

## 5. Free-Key Tiers (Free Signup, No Credit Card)

| Service | Free allotment | Covers |
|---|---|---|
| **CoinGecko Demo** | 10K calls/mo, 100 req/min | 50–60+ endpoints, 1 yr daily history |
| **CoinMarketCap Basic** | 15K credits/mo, 50 req/min | 63 endpoints |
| **CryptoCompare / CCData** | ⚠️ Free tier retired May 2026 — now sales-only | — |
| **CoinCap v3** | Free key (replaces keyless v2) | Real-time prices, assets, rates |
| **Birdeye** | 30K CU/mo, 1 req/s | Solana/multi-chain token prices, OHLCV, liquidity, wallet PnL |
| **CoinStats API** | 20K credits/mo | Market + wallet + portfolio + token security |
| **Mobula** | Free tier | Multi-chain market + wallet data |
| **Codex.io (Defined)** | Free tier | Pair/token data, websockets |
| **Alchemy** | 30M CUs/mo, 15 req/s, 5 apps/webhooks | 30+/100+ chains, Token/NFT/Transfer APIs, archive access |
| **Infura** | 3M credits/day, 500 credits/s | 40+ networks, Ethereum + L2s |
| **Chainstack** | 3M RUs/mo, 25 req/s, 1 project | 70+ chains, WebSockets |
| **Helius (Solana)** | 1M credits/mo, 10 RPC req/s, 2 DAS req/s | RPC + DAS + enhanced APIs, webhooks, archive |
| **QuickNode** | 10M API credits/mo, 15 req/s | 80+ chains |
| **NOWNodes** | 100K requests/mo, 1 key | 60+ chains RPC/API |
| **GetBlock** | Free shared-node package | 130+ chains RPC |
| **Tatum** | 3 req/s, 100K lifetime credits, 2 keys | 130+ networks, unified Data API/RPC |
| **Etherscan family** (Etherscan, BscScan, Polygonscan, Arbiscan, Basescan, Tronscan, etc.) | 5 calls/sec, 100K calls/day | 60+ EVM chains via `chainid`; some newer chains share a pooled quota |
| **Flipside Crypto** | Free SDK/query tier | SQL over curated multi-chain tables |
| **The Graph / Subgraph Studio** | Free monthly query allowance | Indexed EVM/Solana subgraphs via GraphQL + Token API |
| **Dune Analytics** | Free credits exist, but API is largely execution-gated | ⚠️ View-only on free plan; paid Analyst plan ($75/mo) or 14-day trial for real API access |
| **Coin Metrics Community API** | Free community tier | Network/on-chain community metrics |
| **Blockchair API** | Free tier, daily quota | Multi-chain (Bitcoin + 17+ networks) |
| **Messari API** | Limited free/keyless endpoints | Crypto metrics, research — heavily rate-limited |
| **Santiment (SanAPI)** | ~1,000 calls/mo, 100 req/min | On-chain, social, developer-activity metrics |
| **LunarCrush API** | Free tier (rate-limited) | Social sentiment, Galaxy Score, influencer data |
| **Glassnode** | Free community metrics (Tier 1, daily) | On-chain metrics (full API is paid) |
| **CryptoQuant** | Free basic | Exchange flows, MVRV, funding |
| **Moralis / Nodit / dRPC / BlockPI / Chainbase / Covalent GoldRush** | Various free/freemium credit tiers | Multi-chain Web3 data APIs |
| **OpenSea API / Magic Eden API** | Free keys, rate-limited | NFT collections, listings (OpenSea also has paid x402 endpoints) |
| **Reservoir / SimpleHash** | Free tier | NFT liquidity/metadata, multi-chain NFT metadata |
| **Neynar** | Free tier | Farcaster social graph |
| **beaconcha.in** | Free tier | ETH validator/consensus data |
| **NewsData.io** | Free daily credits | Real-time crypto news, search, headlines |
| **CryptoPanic** | ⚠️ Free developer JSON API discontinued — RSS feeds remain free | News aggregation |
| **Octav** | Free portfolio API tier | 20+ chains, DeFi positions |
| **CoinAPI** | $25 one-time credits (not recurring) | Tick-level CEX history (prototype-scale) |

---

## 6. Blockchain RPC / Node Infrastructure (Free, Keyless)

| Service | Endpoint pattern | Coverage |
|---|---|---|
| **PublicNode** | `ethereum-rpc.publicnode.com`, `bitcoin-rpc.publicnode.com`, `solana-rpc.publicnode.com`, etc. | 30–78 chains, keyless RPC + WS |
| **Ankr Public RPC** | `rpc.ankr.com/<chain>` | 70+ networks (Freemium 200M credits/mo with account) |
| **LlamaNodes / LlamaRPC** | `eth.llamarpc.com` (+ other chains) | Ethereum + major chains |
| **Cloudflare Ethereum Gateway** | `cloudflare-eth.com` | Ethereum |
| **1inch RPC** | `rpc.1inch.io/eth` | Ethereum |
| **BlastAPI Public** | `eth-mainnet.public.blastapi.io` | Multiple EVM chains |
| **SolidRPC Public** | `rpc.solidrpc.io/public/evm/{chainId}` | Ethereum, Optimism, BSC, Polygon, Base, Arbitrum, Avalanche, Robinhood Chain |
| **1RPC** | — | Multi-chain, privacy-focused |
| **Solana Public RPC** (mainnet + devnet) | `api.mainnet-beta.solana.com`, `api.devnet.solana.com` | Solana (100 req/10s/IP, 40 req/10s/RPC) |
| **Chainlist.org** | directory | Metadata of free endpoints per chain |
| **Flashbots Protect** | `rpc.flashbots.net` | Ethereum, MEV protection |

---

## 7. On-Chain Analytics / Bulk Datasets

| Service | Access |
|---|---|
| **Dune Analytics** | Free credits exist but view-only on free plan; needs paid plan or trial for execution; MCP available |
| **Flipside Crypto** | Free SDK/API key, curated multi-chain SQL tables |
| **Google BigQuery Public Datasets** | `crypto_bitcoin`, `crypto_ethereum`, `crypto_polygon`, etc. — free within 1TB/mo query tier |
| **AWS Public Blockchain Data** | Open Data: EVM + Solana datasets |
| **Binance historical data** | `data.binance.vision` — free S3 dumps of klines, trades, aggTrades |
| **Whale Alert historical archive** | `whale-alert.io/whale-alerts-archive.json.gzip` — free downloadable archive (live API is paid) |
| **DefiLlama GitHub repos** | Open-source raw datasets behind the API |
| **CryptoDataDownload** | Free CSVs (OHLCV for major pairs) |
| **Kaggle crypto datasets** | Free with account |
| **Bitcoin Core node (self-hosted)** | 100% free ground truth |
| **Footprint Analytics** | Free, unified chain data |
| **Goldsky Mirror / Envio HyperSync / Subsquid** | Indexers with free tiers / open source |

---

## 8. AI-Agent Toolkits & LLM-Readable Docs

- **`tckr`** (pip package) — aggregates 32 free sources with MCP/LangChain/OpenAI/Claude Agent SDK adapters; 17 sources keyless, graceful provider fallback
- **CCXT / CCXT Pro** — unified exchange REST/WS abstraction (public data free)
- **GOAT SDK** (`goat-sdk/goat`) — 200+ on-chain actions
- **Solana Agent Kit** (`sendaifun/solana-agent-kit`) — 40+ Solana actions
- **viem / ethers / web3.py** — pair with the free RPCs above
- **Bankless AgentKit / Coinbase AgentKit** — open-source agent frameworks
- **`llms.txt` / `llms-free.txt` docs**: DefiLlama (`api-docs.defillama.com/llms-free.txt`), DexPaprika (`docs.dexpaprika.com/llms.txt`), Helius (`helius.dev/docs/.../llms.txt`), GetBlock (`docs.getblock.io/llms.txt`), CoinGecko MCP docs (`docs.coingecko.com/ai-integration/mcp-server`)

---

## ⚠️ 9. Anti-List: Looks Free, Isn't (as of Oct 2026)

| Service | Reality |
|---|---|
| **CryptoCompare / CCData / CoinDesk Data** | Free tier retired May 2026; now sales-only |
| **CoinCap v2 keyless (`api.coincap.io`)** | Retired; moved to keyed `rest.coincap.io/v3` |
| **QuickNode** | No ongoing free tier in some reports — 1-month trial only, then paid (conflicts with other sources citing a 10M credit/mo free plan; verify current status before relying on it) |
| **Moralis** | No free tier in some listings; Starter from $149/mo (conflicts with other sources citing free daily credits — verify at signup) |
| **Bitquery (general API)** | 7-day trial only for some tiers, though the Bitquery MCP has a separate free tier with account |
| **Nomics** | Dead/retired |
| **Kaiko, Amberdata, Glassnode (full API), IntoTheBlock, Nansen, Arkham, Token Terminal (Pro)** | Paid or sales-only for real API access; dashboards may be free on-site |
| **Messari API** | Limited free endpoints exist but heavily rate-limited/research-oriented |
| **Blockscout API** | Moved largely to keyed Pro API in 2026; don't assume anonymous access works everywhere |
| **Dune API/MCP** | Free plan is view-only — no query execution without a paid Analyst plan or trial |
| **Whale Alert API** | No free tier for live alerts ($29.95/mo); only `/status` and the historical archive are free |
| **CryptoPanic Developer (JSON) API** | Free dev plan discontinued; RSS feeds remain free |
| **CoinMarketCap x402 / QuickNode x402 / other x402 MCPs** | Keyless but pay-per-call in USDC — not free |
| **X/Twitter API** | No free crypto firehose; paid tiers only |

---

## Quick-Start Recommended Stack

1. **Prices/market data:** CoinGecko MCP (keyless) + CoinPaprika MCP (keyless)
2. **DEX data:** DexScreener API + DexPaprika API + GeckoTerminal
3. **DeFi analytics:** DefiLlama API
4. **EVM on-chain:** Alchemy free tier or Infura free tier
5. **Solana:** Helius free tier
6. **CEX OHLCV/tickers:** Binance/Coinbase/Kraken public endpoints via CCXT
7. **News/sentiment:** alternative.me Fear & Greed + free-crypto-news / CryptoPanic RSS
8. **Streaming:** Binance/Coinbase/Kraken/mempool.space WebSockets over REST polling where possible
9. **Security gating before any execution:** GoPlus, Honeypot.is, RugCheck

**Rate-limit note:** keyless endpoints are shared-IP pools (CoinGecko ~10–30/min, DexScreener 300/min, Etherscan 3/s) — cache aggressively and chain fallback providers (e.g., CoinGecko → CoinPaprika → CoinLore) so one throttled source doesn't take an agent down.
