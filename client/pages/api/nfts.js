import axios from 'axios';

const chainId = 1;

const { INFURA_API_KEY, INFURA_SECRET_API_KEY } = process.env;

export default async function handler(req, res) {
  try {
    const walletAddress = req.query.wallet;
    const { data } = await axios.get(`https://nft.api.infura.io/networks/${chainId}/accounts/${walletAddress}/assets/nfts`, {
      headers: {
        Authorization: `Basic ${Buffer.from(`${INFURA_API_KEY}:${INFURA_SECRET_API_KEY}`).toString('base64')}`,
      },
    });

    // const nftsInWallet = data.transfers.filter(transfer => transfer.to === walletAddress);

    res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching NFT transfers:', error);
    res.status(500).json({ error: 'Failed to fetch NFTs', message: error.message  });
  }
}