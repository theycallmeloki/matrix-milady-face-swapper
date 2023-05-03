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

function getImageTypeFromBase64(base64String) {
    const regex = /^data:image\/(\w+);base64/;
    const match = regex.exec(base64String);

    if (match) {
        return match[1];
    }

    return null;
}

const Home: NextPage = () => {
    const widthDeterminer = (widthOfWindow: any) => {
        if (widthOfWindow < 500) {
            return '300px';
        } else if (widthOfWindow < 1000) {
            return '500px';
        } else {
            return '800px';
        }
    };

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
    const [dataUrl, setDataUrl] = useState('');


    const [miladys, setMiladys] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            const response = await fetch('/api/sheets');
            // console.log(response)
            const data = await response.json();
            // console.log(data);
            setMiladys(data);
        };

        fetchData();
    }, []);

    console.log(miladys);

    const [selectedIndex, setSelectedIndex] = useState(null);

    const dropzoneRef = useRef(null);

    function findUrlData(url: any) {
        const data = miladys.find((entry: any) => entry.url === url);

        if (data) {
            const x_scale = data.x_scale || "3";
            const y_scale = data.y_scale || "3";
            const x_location = data.x_location || "-1";
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


    useEffect(() => {
        const eventSource = new EventSource('/api/events');

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received event:', data);
        };

        eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
        };

        return () => {
            eventSource.close();
        };
    }, []);

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
                console.log('File dropped:', file);
                console.log('selectedIndex:', selectedIndex);
                console.log('miladys:', miladys);

                let selectedMiladyUrl: string = '';
                if (selectedIndex === null) {
                    alert('Please select a milady before uploading a file.');
                    return;
                } else {
                    selectedMiladyUrl = miladys[selectedIndex].url;
                    // console.log(findUrlData(selectedMiladyUrl));

                }

                const miladyFitData: any = findUrlData(selectedMiladyUrl);
                console.log('miladyFitData', miladyFitData);

                const formData = new FormData();
                formData.append('file', file);
                formData.append('selectedMilady', selectedMiladyUrl);
                formData.append('xScale', miladyFitData.x_scale);
                formData.append('yScale', miladyFitData.y_scale);
                formData.append('xLocation', miladyFitData.x_location);
                formData.append('yLocation', miladyFitData.y_location);

                console.log(formData)

                try {
                    setIsWaitingForDownload(true);
                    const response = await fetch(
                        'http://192.168.0.221:5000/uploadImageOrVideo',
                        {
                            method: 'POST',
                            body: formData,
                        },
                    );
                    if (response.ok) {
                        const base64String = await response.json();
                        const b64keys = Object.keys(base64String);
                        console.log(base64String[b64keys[0]]);
                        const fileName =
                            response.headers
                                .get('Content-Disposition')
                                ?.split('filename=')[1] || 'download.jpg';
                        setUserDownloadLink(
                            'data:image/jpg;base64,' + base64String[b64keys[0]],
                        );
                        // Generate a UUID for the new image
                        // const uuid = crypto.randomUUID();
                        setUserDownloadFilename(fileName);
                        setIsWaitingForDownload(false);
                    } else {
                        console.error(
                            'Error uploading file:',
                            response.statusText,
                        );
                        setIsWaitingForDownload(false);
                    }
                } catch (error) {
                    console.error('Error uploading file:', error);
                    setIsWaitingForDownload(false);
                }
            };

            const myDropzone = new Dropzone(dropzoneRef.current, {
                url: '/upload', // This won't be used, as we process the upload manually
                autoProcessQueue: false, // Disable auto processing
                maxFiles: 1,
                acceptedFiles: 'image/*,video/*', // Accept both image and video files
                init: function () {
                    this.on('addedfile', (file) => {
                        onDrop(file);
                    });
                },
            });

            
        }
    }, [selectedIndex]);

    const handleMiladyClick = (index: any, milady: any) => {
        setSelectedIndex(index);
        console.log('Selected milady:', milady);
        console.log('Selected index:', selectedIndex);
    };

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
                    <br />
                    <br />
                    <br />

                    <div
                        style={{
                            width: '85%',
                            height: '1200px',
                            borderStyle: 'dashed',
                            backgroundColor: 'grey',
                            marginTop: '50px',
                        }}
                    >
                        <div
                            style={{
                                textAlign: 'center',
                                fontSize: '28px',
                                marginTop: '10px',
                            }}
                        >
                            Select a milady!
                        </div>
                        <hr />
                        <div
                            style={{
                                display: 'flex',
                                flexDirection: 'row',
                                justifyContent: 'space-around',
                                flexWrap: 'wrap',
                            }}
                        >
                            {miladys &&
                                Array.isArray(miladys) &&
                                miladys.map((milady, index) => {
                                    const isSelected = selectedIndex === index;
                                    return (
                                        <div
                                            key={milady.url}
                                            style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                alignItems: 'center',
                                                margin: '10px',
                                            }}
                                        >
                                            <img
                                                src={milady.url}
                                                style={{
                                                    width: '100px',
                                                    height: '100px',
                                                    opacity: isSelected
                                                        ? 1
                                                        : 0.25,
                                                }}
                                                onClick={() =>
                                                    handleMiladyClick(
                                                        index,
                                                        milady,
                                                    )
                                                }
                                            />
                                        </div>
                                    );
                                })}
                        </div>
                    </div>

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
                            {userDownloadLink && (
                                <div style={{ textAlign: 'center' }}>
                                    {isWaitingForDownload === true ? (
                                        'Your download will appear here when ready.'
                                    ) : (
                                        <>
                                            <a
                                                href={userDownloadLink}
                                                download={`${crypto.randomUUID()}.jpg`}
                                                style={{
                                                    display: 'inline-block',
                                                    textDecoration: 'none',
                                                }}
                                            >
                                                <img
                                                    src={userDownloadLink}
                                                    alt="milady face swap"
                                                    style={{
                                                        cursor: 'pointer',
                                                    }}
                                                />
                                            </a>
                                        </>
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

            <footer
                style={{
                    textAlign: 'center',
                    fontSize: '28px',
                    borderStyle: 'solid',
                    padding: '10px',
                }}
            >
                Made with ❤️ by your frens{' '}
                <a
                    href="https://twitter.com/chillgates_"
                    rel="noopener noreferrer"
                    target="_blank"
                >
                    @chillgates_
                </a>{' '}
                and{' '}
                <a
                    href="https://twitter.com/SneckoAye"
                    rel="noopener noreferrer"
                    target="_blank"
                >
                    @SneckoAye
                </a>{' '}
                🚀
            </footer>
        </div>
    );
};

export default Home;
