import React from "react";
import { Helmet } from "react-helmet";

import "./../styles/global.scss";
import IndexPage from "./index";
import DashPage from "./dash";
import PrivacyPage from "./privacy";
import { Switch, Route, Router } from "./../util/router.js";
import NotFoundPage from "./not-found.js";
import "./../util/analytics.js";

function App(props) {
  return (
    <Router>
      <Helmet>
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
        {/* <meta name="og:image" content="https://brorender.site/img/logo.png" /> */}
      </Helmet>
      <Switch>
        <Route exact path="/" component={IndexPage} />
        {/* <Route path="/brorender-site/" component={IndexPage} /> */}
        {/* <Route exact path="/privacy" component={PrivacyPage} /> */}
        {/* <Route path="/dash" component={DashPage} /> */}
        <Route component={NotFoundPage} />
      </Switch>
    </Router>
  );
}

export default App;
