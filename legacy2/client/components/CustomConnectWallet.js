import React, { useState, useEffect, useCallback } from "react";
import { ConnectButton } from "@rainbow-me/rainbowkit";

const withWalletButtonContent = (Component) => {
  const WrappedComponent = ({ onWalletAddressChange, ...props }) => {
    const handleAddressChange = useCallback(
      (account) => {
        if (account && account.address) {
          onWalletAddressChange(account.address);
          console.log("Connected wallet address:", account.address);
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
          console.log("Wallet address:", connectedAccount.address);
        }
      } catch (error) {
        console.error("Error connecting wallet:", error);
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
  WrappedComponent.displayName = `withWalletButtonContent(${
    Component.displayName || Component.name || "Component"
  })`;
  return WrappedComponent;
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
    const ready = mounted && authenticationStatus !== "loading";
    const connected =
      ready &&
      account &&
      chain &&
      (!authenticationStatus || authenticationStatus === "authenticated");

    if (!connected) {
      return (
        <button
          onClick={handleSignInClick}
          type="button"
          style={{
            fontSize: "25px",
            background: "linear-gradient(180deg, #383838 0%, #292929 100%)",
            color: "#FFFFFF",
            borderRadius: "5px",
            padding: "10px 20px",
            boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.25)",
            border: "none",
            outline: "none",
          }}
        >
          Sign in
        </button>
      );
    }

    return (
      <button
        onClick={openAccountModal}
        type="button"
        style={{
          fontSize: "25px",
          background: "linear-gradient(180deg, #383838 0%, #292929 100%)",
          color: "#FFFFFF",
          borderRadius: "5px",
          padding: "10px 20px",
          boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.25)",
          border: "none",
          outline: "none",
        }}
      >
        {account.displayName}
        {account.displayBalance ? ` (${account.displayBalance})` : ""}
      </button>
    );
  }
);

export const CustomConnectWallet = ({ onWalletAddressChange }) => {
  return (
    <ConnectButton.Custom>
      {(props) => (
        <WalletButtonContent
          {...props}
          onWalletAddressChange={onWalletAddressChange}
        />
      )}
    </ConnectButton.Custom>
  );
};

export default CustomConnectWallet;
