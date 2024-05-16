import axios from 'axios';

const chainId = 1;

const { INFURA_API_KEY, INFURA_SECRET_API_KEY } = process.env;

export default async function handler(req, res) {
  try {
    const walletAddress = req.query.wallet;

    let allNFTs = [];
    let nextCursor = '';

    const headers = {
      Authorization: `Basic ${Buffer.from(`${INFURA_API_KEY}:${INFURA_SECRET_API_KEY}`).toString('base64')}`,
    };

    while (true) {
      const { data } = await axios.get(`https://nft.api.infura.io/networks/${chainId}/accounts/${walletAddress}/assets/nfts?cursor=${nextCursor}`, {
        headers,
      });

      allNFTs = allNFTs.concat(data.assets);

      if (data.pagination && data.pagination.cursor) {
        nextCursor = data.pagination.cursor;
      } else {
        break;
      }
    }

    res.status(200).json({ assets: allNFTs });
  } catch (error) {
    console.error('Error fetching NFT transfers:', error);
    res.status(500).json({ error: 'Failed to fetch NFTs', message: error.message });
  }
}
