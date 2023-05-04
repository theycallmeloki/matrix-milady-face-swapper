import React, { useState, useEffect } from 'react';
import { ConnectButton } from '@rainbow-me/rainbowkit';

export const CustomConnectWallet = ({ onWalletAddressChange }) => {
  const [connectedAddress, setConnectedAddress] = useState(null);
  
  return (
    <ConnectButton.Custom>
      {({
        account,
        chain,
        openAccountModal,
        openChainModal,
        openConnectModal,
        authenticationStatus,
        mounted,
        }) => {
        useEffect(() => {
          if (account && account.address) {
              setConnectedAddress(account.address);
              onWalletAddressChange(account.address);
              console.log('Connected wallet address:', account.address);
          }
        }, [account, onWalletAddressChange]);
        const ready = mounted && authenticationStatus !== 'loading';
        const connected =
          ready &&
          account &&
          chain &&
          (!authenticationStatus ||
            authenticationStatus === 'authenticated');

        const handleSignInClick = async () => {
            try {
                const connectedAccount = await openConnectModal();
                if (connectedAccount) {
                console.log('Wallet address:', connectedAccount.address);
                }
            } catch (error) {
                console.error('Error connecting wallet:', error);
            }
        };

        return (
          <div
            {...(!ready && {
              'aria-hidden': true,
              'style': {
                opacity: 0,
                pointerEvents: 'none',
                userSelect: 'none',
              },
            })}
          >
            {(() => {
              if (!connected) {
                return (
                  <button onClick={handleSignInClick} type="button">
                    Sign in
                  </button>
                );
              }

              return (
                <div>
                  <button onClick={openAccountModal} type="button">
                    {account.displayName}
                    {account.displayBalance
                      ? ` (${account.displayBalance})`
                      : ''}
                  </button>
                </div>
              );
            })()}
          </div>
        );
      }}
    </ConnectButton.Custom>
  );
};

export default CustomConnectWallet;