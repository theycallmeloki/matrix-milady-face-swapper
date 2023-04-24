import React, {
    useEffect,
    useState,
    useCallback,
    useReducer,
    useRef,
} from 'react';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import type { NextPage } from 'next';
import Head from 'next/head';
import styles from '../styles/Home.module.css';
import NavbarCustom from '../components/NavbarCustom';
import HeroSection from '../components/HeroSection';
import Footer from '../components/Footer';
import Dropzone from 'dropzone';
import Image from 'next/image';
// import "dropzone/dist/min/dropzone.min.css";

const Home: NextPage = () => {

    const widthDeterminer = (widthOfWindow: any) => {
        if (widthOfWindow < 500) {
            return '300px';
        } else if (widthOfWindow < 1000) {
            return '500px';
        } else {
            return '800px';
        }
    }

    const [windowWidth, setWindowWidth] = useState(null);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            setWindowWidth(window.innerWidth);

            const handleResize = () => {
                setWindowWidth(window.innerWidth);
            };

            window.addEventListener('resize', handleResize);
            return () => {
                window.removeEventListener('resize', handleResize);
            };
        }
    }, []);

    const [downloadLink, setDownloadLink] = useState('');
    const [isWaitingForDownload, setIsWaitingForDownload] = useState(false);
    const [userDownloadLink, setUserDownloadLink] = useState('');
    const [userDownloadFilename, setUserDownloadFilename] = useState('');

    const dropzoneRef = useRef(null);

    const onDrop = (acceptedFiles: any) => {
        // Handle dropped files
    };

    React.useEffect(() => {
        if (dropzoneRef.current) {
            // Check if there's an existing Dropzone instance and destroy it
            if (Dropzone.instances.length > 0) {
                Dropzone.instances.forEach((instance) => {
                    if (instance.element === dropzoneRef.current) {
                        instance.destroy();
                    }
                });
            }

            const myDropzone = new Dropzone(dropzoneRef.current, {
                url: '/upload', // Set your server URL here
                autoProcessQueue: true,
                maxFiles: 1, // Limit to 1 file at a time
                acceptedFiles: 'image/*', // Accept only image files
                init: function () {
                    this.on('addedfile', (file) => {
                        onDrop(file);
                    });
                },
            });
        }
    }, []);

    return (
        <div className={styles.container}>
            <Head>
                <meta charSet="utf-8" />
                <title>Nutter Tools</title>
                <link rel="canonical" href="https://nutter.tools" />
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
                    content="Nutter Tools - Swap faces with milady, remilio, radbro!"
                />
            </Head>

            <main className={styles.main}>
                <ConnectButton />
                <br />
                <br />
                <hr style={{ width: '100%' }} />
                <br />
                <br />

                <div>
                    {windowWidth && (
                        <img
                            src="https://i.imgur.com/3O9l9se.png"
                            style={{ width: widthDeterminer(windowWidth) }}
                        />
                    )}
                </div>

                <br />
                <hr style={{ width: '100%' }} />
                <br />
                <br />
                <br />

                <div
                    style={{
                        backgroundColor: 'black',
                        color: '#0f0',
                        width: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                    }}
                >
                    <div style={{ paddingTop: '75px' }}>
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
                    <br />

                    <div
                        style={{
                            marginLeft: 'auto',
                            marginRight: 'auto',
                            marginTop: '2em',
                            backgroundImage: 'url(img/dragdrop-header.gif)',
                            backgroundSize: '80%',
                            backgroundPosition: 'center',
                        }}
                    >
                        <form
                            ref={dropzoneRef}
                            id="blendDropzone"
                            className="dropzone dz-clickable"
                            style={{
                                border: '5px grey dashed',
                                borderRadius: '10px',
                                minHeight: '75vh',
                                width: '80vw',
                                padding: '20px',
                            }}
                        >
                            {downloadLink !== '' && (
                                <div style={{ textAlign: 'center' }}>
                                    {isWaitingForDownload === true ? (
                                        'Your download will appear here when ready.'
                                    ) : (
                                        <a
                                            href={userDownloadLink}
                                            download={userDownloadFilename}
                                        >
                                            <button type="button">
                                                Download
                                            </button>
                                        </a>
                                    )}
                                </div>
                            )}
                        </form>
                        <br />
                        <br />
                        <br />
                    </div>
                </div>
            </main>

            <footer className={styles.footer}>
                <a
                    href="https://rainbow.me"
                    rel="noopener noreferrer"
                    target="_blank"
                >
                    Made with ❤️ by your frens at 🌈
                </a>
            </footer>
        </div>
    );
};

export default Home;
