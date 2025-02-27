# Entra-Pass-Spray

## Use the entrapassspray python script in the runbook to execute the attack.

The Entra-Pass-Spray Python script is designed to execute a password spray attack on Microsoft Entra ID using Azure Runbooks.
### How It Works
- The script runs within an Azure Runbook, making the attack appear as if it's originating from Microsoft's own infrastructure.
- This helps evade detection since, in the victim's logs, the source of the attack will show as a Microsoft IP address instead of an external threat.

### For more information:
https://medium.com/@matanb707/entra-pass-spray-1d47325faa32

### Credits

Beau Bullock - dafthack
