import axios from 'axios';

const chainId = 1;
const fromBlock = 16026179;
const toBlock = 16026190;
const Auth = process.env.INFURA_API_KEY;

export default async function handler(req, res) {
  try {
    const { data } = await axios.get(`https://nft.api.infura.io/networks/${chainId}/nfts/transfers?fromBlock=${fromBlock}&toBlock=${toBlock}`, {
      headers: {
        Authorization: `Basic ${Auth}`,
      },
    });

    const walletAddress = req.query.wallet;
    const nftsInWallet = data.transfers.filter(transfer => transfer.to === walletAddress);

    res.status(200).json(nftsInWallet);
  } catch (error) {
    console.error('Error fetching NFT transfers:', error);
    res.status(500).json({ error: 'Failed to fetch NFT transfers' });
  }
}