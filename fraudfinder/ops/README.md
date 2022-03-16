## This module implements the management features of the fraudfinder system.

### Requirements

- model monitoring with appropriate thresholds must be used to alert your operations team about drift and/or skew in production data
- must deliver a test system to generate simulated transaction data on batch and streaming bases. Batches and streams must be tunable such that the tester can simulate a specified distribution of fraudulent transactions.
- must provide a dashboard to monitor various performance and operational aspects of this system

### Deliverables

- three microservices:
  - ff-datagen - the data generator
  - ff-server - the web backend
  - ff-web - the front end UI
- management web app, which uses the back end services to provide these features:
  - view models and endpoints
  - start/stop/status of continuous data feed
  - interactive testing
  - load test - trigger parameterized traffic to test monitoring alerts
  - stretch goal: model perf dashboard - view alerts, skew, drift, latency, prediction errors, XAI attributions (when available), etc., with ability to combine multiple monitoring jobs for direct graphical comparison
  - stretch goal: alerting extension - monitor alerts and forward via pub/sub, eventARC, email, SMS, etc.

