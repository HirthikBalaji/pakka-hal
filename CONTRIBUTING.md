# Contributing to Pakka Hal

We welcome contributions from developers, civic researchers, linguistic experts, and open-source enthusiasts!

## Starter Issues for Contributors
1. **Add `city.yaml` for your city:** Fork the repository, create a configuration file under `config/<city>.yaml`, and submit a PR!
2. **Native-Speaker Review:** Audit Gurmukhi and Devanagari translation prompts, voice transcripts, and UI strings.
3. **Department Adapters:** Build plugins for municipal email dispatchers, CSV batch drops, or SMS gateways.
4. **Reliability Calibration:** Add visual calibration curves for the Bayesian closure verifier.
5. **Low-Bandwidth PWA Mode:** Optimize assets for 2G/3G edge connections in peri-urban areas.

## Development Workflow
1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/pakka-hal.git
   cd pakka-hal
   ```
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Run the test suite:
   ```bash
   python tests/run_tests.py
   ```
4. Run the comprehensive evaluation benchmark:
   ```bash
   python eval/run_eval.py
   ```
5. Launch the application:
   ```bash
   python main.py
   ```
   Open `http://localhost:8000` in your browser.
