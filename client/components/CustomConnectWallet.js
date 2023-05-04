import React, { useState, useEffect, useCallback } from 'react';
import { ConnectButton } from '@rainbow-me/rainbowkit';

const withWalletButtonContent = (Component) => {
  return ({ onWalletAddressChange, ...props }) => {
    const handleAddressChange = useCallback(
      (account) => {
        if (account && account.address) {
          onWalletAddressChange(account.address);
          console.log('Connected wallet address:', account.address);
        }
      },
      [onWalletAddressChange]
    );

    useEffect(() => {
      handleAddressChange(props.account);
    }, [props.account, handleAddressChange]);

    const handleSignInClick = async () => {
      try {
        const connectedAccount = await props.openConnectModal();
        if (connectedAccount) {
          console.log('Wallet address:', connectedAccount.address);
        }
      } catch (error) {
        console.error('Error connecting wallet:', error);
      }
    };

    return (
      <Component
        {...props}
        handleSignInClick={handleSignInClick}
        handleAddressChange={handleAddressChange}
      />
    );
  };
};

const WalletButtonContent = withWalletButtonContent(
  ({
    account,
    chain,
    openAccountModal,
    authenticationStatus,
    mounted,
    handleSignInClick,
  }) => {
    const ready = mounted && authenticationStatus !== 'loading';
    const connected =
      ready &&
      account &&
      chain &&
      (!authenticationStatus || authenticationStatus === 'authenticated');

    if (!connected) {
      return (
        <button onClick={handleSignInClick} type="button" style={{ fontSize: '20px' }}>
          Sign in
        </button>
      );
    }

    return (
      <button onClick={openAccountModal} type="button" style={{ fontSize: '20px' }}>
        {account.displayName}
        {account.displayBalance ? ` (${account.displayBalance})` : ''}
      </button>
    );
  }
);

export const CustomConnectWallet = ({ onWalletAddressChange }) => {
  return (
    <ConnectButton.Custom>
      {(props) => <WalletButtonContent {...props} onWalletAddressChange={onWalletAddressChange} />}
    </ConnectButton.Custom>
  );
};

export default CustomConnectWallet;
