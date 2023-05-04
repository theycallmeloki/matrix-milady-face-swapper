import React, { useEffect, useState, useRef } from "react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import type { NextPage } from "next";
import Head from "next/head";
import Script from "next/script";
import styles from "../styles/Home.module.css";
import Dropzone from "dropzone";
import Image from "next/image";
import WalletConnectProvider from "@walletconnect/web3-provider";
import { ethers } from "ethers";
import CustomConnectWallet from "../components/CustomConnectWallet";

const Home: NextPage = () => {
  const widthDeterminer = (widthOfWindow: any) => {
    if (widthOfWindow < 500) {
      return "300px";
    } else if (widthOfWindow < 1000) {
      return "500px";
    } else {
      return "800px";
    }
  };

  const [windowWidth, setWindowWidth] = useState(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      // @ts-ignore
      setWindowWidth(window.innerWidth);

      const handleResize = () => {
        // @ts-ignore
        setWindowWidth(window.innerWidth);
      };

      window.addEventListener("resize", handleResize);
      return () => {
        window.removeEventListener("resize", handleResize);
      };
    }
  }, []);

  const [isWaitingForDownload, setIsWaitingForDownload] = useState(false);
  const [userDownloadLink, setUserDownloadLink] = useState("");
  const [userDownloadFilename, setUserDownloadFilename] = useState("");

  const [miladys, setMiladys] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const response = await fetch("/api/sheets");
      const data = await response.json();
      setMiladys(data);
    };

    fetchData();
  }, []);

  // console.log(miladys);

  const [selectedIndex, setSelectedIndex] = useState(null);

  const dropzoneRef = useRef(null);

  function findUrlData(url: any) {
    const data = miladys.find((entry: any) => entry.url === url);

    if (data) {
      // @ts-ignore
      const x_scale = data.x_scale || "3";
      // @ts-ignore
      const y_scale = data.y_scale || "3";
      // @ts-ignore
      const x_location = data.x_location || "-1";
      // @ts-ignore
      const y_location = data.y_location || "-1";

      return {
        x_scale,
        y_scale,
        x_location,
        y_location,
      };
    } else {
      return null;
    }
  }

  const fetchNFTs = async (walletAddress: string) => {
    try {
      const response = await fetch(`/api/nfts?wallet=${walletAddress}`);
      const data = await response.json();
      // console.log('NFTs in possession:', data);
      return data.assets;
    } catch (error) {
      console.error("Error fetching NFTs:", error);
      return [];
    }
  };


  useEffect(() => {
    if (dropzoneRef.current) {
      if (Dropzone.instances.length > 0) {
        Dropzone.instances.forEach((instance) => {
          if (instance.element === dropzoneRef.current) {
            instance.destroy();
          }
        });
      }

      const onDrop = async (file: any) => {
        console.log("File dropped:", file);
        console.log("selectedIndex:", selectedIndex);
        console.log("miladys:", miladys);

        if (!userIsOg) {
          alert(
            "Sorry, only OGs can upload files. OGs are holders of Miladys, Remilios, Radbro Webring and Matrix Milady."
          );
          return;
        }

        let selectedMiladyUrl: string = "";
        if (selectedIndex === null) {
          alert("Please select a milady before uploading a file.");
          return;
        } else {
          // @ts-ignore
          selectedMiladyUrl = miladys[selectedIndex].url;
          // console.log(findUrlData(selectedMiladyUrl));
        }

        const miladyFitData: any = findUrlData(selectedMiladyUrl);
        console.log("miladyFitData", miladyFitData);

        const formData = new FormData();
        formData.append("file", file);
        formData.append("selectedMilady", selectedMiladyUrl);
        formData.append("xScale", miladyFitData.x_scale);
        formData.append("yScale", miladyFitData.y_scale);
        formData.append("xLocation", miladyFitData.x_location);
        formData.append("yLocation", miladyFitData.y_location);

        console.log(formData);

        try {
          setIsWaitingForDownload(true);
          const response = await fetch(
            "https://api.matrixmilady.com/uploadImageOrVideo",
            {
              method: "POST",
              body: formData,
            }
          );
          if (response.ok) {
            const base64String = await response.json();
            const b64keys = Object.keys(base64String);
            console.log(base64String[b64keys[0]]);
            const fileName =
              response.headers
                .get("Content-Disposition")
                ?.split("filename=")[1] || "download.jpg";
            setUserDownloadLink(
              "data:image/jpg;base64," + base64String[b64keys[0]]
            );
            // Generate a UUID for the new image
            // const uuid = crypto.randomUUID();
            setUserDownloadFilename(fileName);
            setIsWaitingForDownload(false);
          } else {
            console.error("Error uploading file:", response.statusText);
            setIsWaitingForDownload(false);
          }
        } catch (error) {
          console.error("Error uploading file:", error);
          setIsWaitingForDownload(false);
        }
      };

      const myDropzone = new Dropzone(dropzoneRef.current, {
        url: "/upload", // This won't be used, as we process the upload manually
        autoProcessQueue: false, // Disable auto processing
        maxFiles: 1,
        acceptedFiles: "image/*,video/*", // Accept both image and video files
        init: function () {
          this.on("addedfile", (file) => {
            onDrop(file);
          });
        },
      });
    }
  }, [selectedIndex]);

  const handleMiladyClick = (index: any, milady: any) => {
    setSelectedIndex(index);
    console.log("Selected milady:", milady);
    console.log("Selected index:", selectedIndex);
  };

  const [walletAddress, setWalletAddress] = useState(null);
  const [userIsOg, setUserIsOg] = useState(false);

  useEffect(() => {
    if (walletAddress) {
      const fetchAndUpdateNFTs = async () => {
        const sourcedNFTs = await fetchNFTs(walletAddress);
        console.log(sourcedNFTs);
        sourcedNFTs.forEach((nft: any) => {
          console.log(nft);
          console.log("looking at ", nft.contract);
          if (
            nft.contract === "0x5Af0D9827E0c53E4799BB226655A1de152A425a5" ||
            nft.contract === "0x4246200d62072cf8836f1062a115927555b9c497" ||
            nft.contract === "0xABCDB5710B88f456fED1e99025379e2969F29610" ||
            nft.contract === "0xD3D9ddd0CF0A5F0BFB8f7fcEAe075DF687eAEBaB"
          ) {
            console.log(
              nft.contract === "0x5Af0D9827E0c53E4799BB226655A1de152A425a5",
              "milady"
            );
            console.log(
              nft.contract === "0x4246200d62072Cf8836F1062A115927555B9C497",
              "milady matrix"
            );
            console.log(
              nft.contract === "0xABCDB5710B88f456fED1e99025379e2969F29610",
              "radbro"
            );
            console.log(
              nft.contract === "0xD3D9ddd0CF0A5F0BFB8f7fcEAe075DF687eAEBaB",
              "remilio"
            );
            setUserIsOg(true);
          }
        });
      };
      fetchAndUpdateNFTs();
    }
  }, [walletAddress]);

  const handleWalletAddressChange = async (address: any) => {
    console.log("Parent received wallet address:", address);
    // do the nft lookup call only once, and store the results in a state variable setFetchedNFTs and setUserOwnedNFTs
    setWalletAddress(address);
  };

  return (
    <div className={styles.container}>
      <Head>
        <meta charSet="utf-8" />
        <title>Matrix Milady - Nutter Tools</title>
        <link rel="canonical" href="https://matrixmilady.com" />
        <meta name="author" content="ogmilady" />
        <meta
          name="keywords"
          content="matrix, milady, distributed, free, online, face, swap"
        />
        <meta
          name="description"
          content="Swap faces with milady, remilio, radbro!"
        />
        <meta
          name="og:description"
          content="Swap faces with milady, remilio, radbro!"
        />
        <meta
          name="og:title"
          content="Matrix Milady - Swap faces with milady, remilio, radbro!"
        />
      </Head>
      <Script id="google-tag-manager" strategy="afterInteractive">
        {`
          (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
          new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
          j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
          'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
          })(window,document,'script','dataLayer','G-C5GF7QCHTV');
        `}
      </Script>
      <Script
        id="google-tag-gtag"
        src="https://www.googletagmanager.com/gtag/js?id=G-C5GF7QCHTV"
        strategy="afterInteractive"
        async
      />

      <Script id="google-tag-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'G-C5GF7QCHTV');
        `}
      </Script>

      <main className={styles.main}>
        {/* <ConnectButton label="Sign in" accountStatus="address" /> */}
        <CustomConnectWallet
          onWalletAddressChange={handleWalletAddressChange}
        />
        <br />
        <br />
        <hr style={{ width: "100%" }} />
        <br />
        <br />

        {/* <div>
          {windowWidth && (
            <img
              src="https://i.imgur.com/3O9l9se.png"
              style={{ width: widthDeterminer(windowWidth) }}
            />
          )}
        </div>

        <br />
        <hr style={{ width: "100%" }} />
        <br />
        <br />
        <br /> */}

        <div
          style={{
            backgroundColor: "black",
            color: "#0f0",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div style={{ paddingTop: "75px" }}>
            {windowWidth && (
              <img
                src="https://i.imgur.com/OS4quT2.png"
                style={{
                  width: widthDeterminer(windowWidth / 2),
                }}
              />
            )}
          </div>

          <br />

          <div
            style={{
              marginLeft: "auto",
              marginRight: "auto",
              marginTop: "2em",
              backgroundSize: "80%",
              backgroundPosition: "center",
            }}
          >
            <div
              style={{
                backgroundColor: "white",
                marginTop: "50px",
                borderRadius: "20px",
              }}
            >
              <div
                style={{
                  textAlign: "center",
                  fontSize: "28px",
                  marginTop: "10px",
                }}
              >
                Select a milady/remilio/radbro!
              </div>
              <hr />
              <div
                style={{
                  display: "flex",
                  flexDirection: "row",
                  justifyContent: "space-around",
                  flexWrap: "wrap",
                }}
              >
                {miladys &&
                  Array.isArray(miladys) &&
                  miladys.map((milady: any, index: any) => {
                    const isSelected = selectedIndex === index;
                    return (
                      <div
                        key={milady.url}
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          margin: "10px",
                        }}
                      >
                        <img
                          src={milady.url}
                          style={{
                            width: "100px",
                            height: "100px",
                            opacity: isSelected ? 1 : 0.25,
                          }}
                          onClick={() => handleMiladyClick(index, milady)}
                        />
                      </div>
                    );
                  })}
              </div>
            </div>
            <form
              ref={dropzoneRef}
              id="blendDropzone"
              className="dropzone dz-clickable"
              style={{
                border: "5px grey dashed",
                borderRadius: "10px",
                marginTop: "50px",
                padding: "20px",
              }}
            ></form>

            <br />
            {(userDownloadLink || isWaitingForDownload) && (
              <div
                style={{
                  textAlign: "center",
                  backgroundColor: "white",
                  marginTop: "50px",
                  borderRadius: "20px",
                  padding: '20px',
                  fontSize: '20px',
                  color: 'black'
                }}
              >
                {isWaitingForDownload === true ? (
                  "Your download will appear here when ready. (Click to download!)"
                ) : (
                  <>
                    <a
                      href={userDownloadLink}
                      download={`${crypto.randomUUID()}.jpg`}
                      style={{
                        display: "inline-block",
                          textDecoration: "none",
                          borderStyle: 'solid', 
                          padding: '10px',
                          borderRadius: '10px',
                            backgroundColor: 'black',
                      }}
                    >
                      <img
                        src={userDownloadLink}
                        alt="milady face swap"
                        style={{
                          cursor: "pointer",
                        }}
                      />
                    </a>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      <footer
        style={{
          textAlign: "center",
          fontSize: "28px",
          borderStyle: "solid",
          padding: "10px",
        }}
      >
        Made with ❤️ by your frens{" "}
        <a
          href="https://twitter.com/chillgates_"
          rel="noopener noreferrer"
          target="_blank"
        >
          @chillgates_
        </a>{" "}
        and{" "}
        <a
          href="https://twitter.com/SneckoAye"
          rel="noopener noreferrer"
          target="_blank"
        >
          @SneckoAye
        </a>{" "}
        🚀
      </footer>
    </div>
  );
};

export default Home;
