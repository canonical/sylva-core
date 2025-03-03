/*
Copyright © 2024 Antoine Monlong <antoine.monlong@orange.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"errors"
	"fmt"
	"os"
	"os/exec"


	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
)

var (
	infraprovider     string
	bootstrapprovider string
	deploymentName    string
	genericName       string

	initCmd = &cobra.Command{
		Use:     "initialize",
		Aliases: []string{"init", "i", "setup", "s", "create", "c"},
		Short:   "Guides user to initialize a new sylva deployment",
		Long:    `This command will guide the user to initialize a new sylva deployment.
		It describes the entire workflow required to deploy a new sylva management cluster and workloads with a clean and documented UX.
		Steps are:
		- Requirements checking (command 'requirements')
		- Configuration (command 'config')
		- Troubleshooting values and potential errors (command 'troubleshoot')
		- Deploying (command 'deploy')
		- Status (command 'status')`,
		Run: func(cmd *cobra.Command, args []string) {

			// Multi-phases command

			// 1. Requirements

			requirementsCmd.Run(cmd, []string{""})

			// 2. Configuration

			// 3. Troubleshoot

			// 4. Deploy

			// 5. Status

			
			requirementsCmd.Run(cmd, []string{""})
			bootstrapprovider = chooseBootstrapProvider()
			infraprovider = chooseInfraProvider()
			genericName = bootstrapprovider + "-" + infraprovider
			deploymentName = chooseDeploymentName("sylva-" + genericName)

			fmt.Println("You choose the following options:")
			fmt.Println("  - Bootstrap Provider:", bootstrapprovider)
			fmt.Println("  - Infrastructure Provider:", infraprovider)
			fmt.Println("  - Deployment Name:", deploymentName)

			prompt := promptui.Prompt{
				Label:     "Would you like to proceed with the initialization? (y/n)",
				IsConfirm: true,
			}
			proceed, err := prompt.Run()
			if err != nil {
				fmt.Printf("Prompt failed %v\n", err)
			}
			if proceed == "y" || proceed == "yes" {
				fmt.Println("Downloading sylva-core")
				cloneRepo("https://gitlab.com/sylva-projects/sylva-core.git")

				fmt.Println("Moving into sylva-core directory")
				err = os.Chdir("sylva-core")
				if err != nil {
					fmt.Println("Failed to change directory to sylva-core:", err)
					os.Exit(1)
				}

				fmt.Println("Copying deployment value for", deploymentName)
				copyDeploymentValues(genericName, deploymentName)

				printWarnings(bootstrapprovider, infraprovider, deploymentName)

				// fmt.Println("Values copied successfully in /environment-values/" + deploymentName)
			} else {
				fmt.Println("Initialization aborted")
			}
		},
	}
)

func init() {
	rootCmd.AddCommand(initCmd)
	
	// rootCmd.Run(requirementsCmd, []string{""})

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// initCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// initCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func chooseBootstrapProvider() string {
	prompt := promptui.Select{
		Label: "Choose the Bootstrap Provider",
		Items: []string{"kubeadm", "rke2"},
	}

	_, result, err := prompt.Run()

	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}

	fmt.Printf("You choose %q\n", result)
	return result
}

func chooseInfraProvider() string {
	prompt := promptui.Select{
		Label: "Choose the Infrastructure Provider",
		Items: []string{"capd", "capm3", "capo", "capv"},
	}

	_, result, err := prompt.Run()

	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}

	fmt.Printf("You choose %q\n", result)
	return result
}

func chooseDeploymentName(defaultValue string) string {
	validate := func(input string) error {
		if len(input) < 3 {
			return errors.New("deployment name must have more than 3 characters")
		}
		return nil
	}

	prompt := promptui.Prompt{
		Label:     "Choose the Deployment Name",
		Validate:  validate,
		Default:   defaultValue,
		AllowEdit: true,
	}

	result, err := prompt.Run()

	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}

	fmt.Printf("You choose %q\n", result)
	return result
}

func cloneRepo(repoURL string) {
	cmd := exec.Command("git", "clone", repoURL)
	err := cmd.Run()
	if err != nil {
		// log.Fatalf("Failed to clone repository: %v", err)
		fmt.Printf("cloneRepo failed %v\n", err)
	}
	fmt.Println("Repository cloned successfully")
}

func copyDeploymentValues(genericName string, deploymentName string) {
	// Copy deployment values
	cmd := exec.Command("cp", "-r", "-n", "environment-values/"+genericName+"/.", "environment-values/"+deploymentName)
	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to copy environment values:", err)
		// os.Exit(1)
	}
}

func printWarnings(bootstrapProvider string, infraProvider string, deploymentName string) {
	fmt.Println(`
	====================================
			   General Warnings
	====================================`)
	fmt.Println("  - Make sure you have set the necessary proxies")
	setProxies(deploymentName)

	if bootstrapProvider == "kubeadm" {
		fmt.Println(`
	====================================
			   KUBEADM WARNINGS
	====================================`)

	} else if bootstrapProvider == "rke2" {
		fmt.Println(`
	====================================
			   RKE2 WARNINGS			
	====================================`)
	}

	if infraProvider == "capd" {
		fmt.Println(`CAPD WARNINGS`)
		fmt.Println("  - \"cluster_virtual_ip\" is not set in the values.yaml file")
		setClusterVirtualIp(deploymentName)

	} else if infraProvider == "capm3" {
		fmt.Println(`
	====================================
			   CAPM3 WARNINGS			
	====================================`)
	} else if infraProvider == "capo" {
		fmt.Println(`
	====================================
			   CAPO WARNINGS			
	====================================`)
		fmt.Println("  - \"clouds_yaml\" is not set in the secrets.yaml file, it's necessary for a capo deployment")
		setCloudsYaml(deploymentName)
	} else if infraProvider == "capv" {
		fmt.Println(`
	====================================
			   CAPV WARNINGS			
	====================================`)
	}
}

func setClusterVirtualIp(deploymentName string) {
	prompt := promptui.Select{
		Label: "Choose an option",
		Items: []string{"Set cluster_virtual_ip", "Access documentation"},
	}
	_, result, err := prompt.Run()
	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}
	switch result {
	case "Set cluster_virtual_ip":
		cmd := exec.Command("bash", "-c", `
		if ! docker network inspect kind > /dev/null 2>&1; then
		  echo "Docker network 'kind' doesn't exist. Creating the network..."
		  docker network create kind
		fi
		
		KIND_PREFIX=$(docker network inspect kind -f '{{ (index .IPAM.Config 0).Subnet }}')
		CLUSTER_IP=$(echo $KIND_PREFIX | awk -F"." '{print $1"."$2"."$3".100"}')
		echo $CLUSTER_IP
		yq -i ".cluster_virtual_ip = \"$CLUSTER_IP\"" environment-values/`+deploymentName+`/values.yaml`)
		cmd.Run()
	case "Access documentation":
		fmt.Println("Documentation: https://example.com")
	}
}

func setProxies(deploymentName string) {
	prompt := promptui.Select{
		Label: "Choose an option",
		Items: []string{"Use system proxies (/etc/environment)", "Set custom proxies", "Access documentation"},
	}
	index, _, err := prompt.Run()
	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}
	switch index {
	case 0:
		fmt.Println("Using system proxies")
		http_proxy := os.Getenv("http_proxy")
		https_proxy := os.Getenv("https_proxy")
		no_proxy := os.Getenv("no_proxy")
		fmt.Println("http_proxy:", http_proxy)
		fmt.Println("https_proxy:", https_proxy)
		fmt.Println("no_proxy:", no_proxy)
		cmd := exec.Command("bash", "-c", `yq -i '.proxies.http_proxy = "`+http_proxy+`" | .proxies.https_proxy = "`+https_proxy+`" | .proxies.no_proxy = "`+no_proxy+`"' environment-values/`+deploymentName+`/values.yaml`)
		cmd.Run()

	case 1:
		cmd := exec.Command("bash", "-c", `echo "Setting custom proxies"`)
		cmd.Run()
		proxyPrompt := promptui.Prompt{
			Label: "Enter the HTTP proxy",
		}
		httpProxy, err := proxyPrompt.Run()
		if err != nil {
			fmt.Printf("Prompt failed %v\n", err)
		}

		proxyPrompt.Label = "Enter the HTTPS proxy"
		httpsProxy, err := proxyPrompt.Run()
		if err != nil {
			fmt.Printf("Prompt failed %v\n", err)
		}

		proxyPrompt.Label = "Enter the no proxy"
		noProxy, err := proxyPrompt.Run()
		if err != nil {
			fmt.Printf("Prompt failed %v\n", err)
		}

		fmt.Println("You entered the following proxies:")
		fmt.Println("  - HTTP Proxy:", httpProxy)
		fmt.Println("  - HTTPS Proxy:", httpsProxy)
		fmt.Println("  - No Proxy:", noProxy)

		prompt := promptui.Prompt{
			Label:     "Would you like to proceed with these proxies? (y/n)",
			IsConfirm: true,
		}
		proceed, err := prompt.Run()
		if err != nil {
			fmt.Printf("Prompt failed %v\n", err)
		}
		if proceed == "y" || proceed == "yes" {
			cmd := exec.Command("bash", "-c", `yq -i '.proxies.http_proxy = "`+httpProxy+`" | .proxies.https_proxy = "`+httpsProxy+`" | .proxies.no_proxy = "`+noProxy+`"' environment-values/`+deploymentName+`/values.yaml`)
			cmd.Run()
		}
	case 2:
		fmt.Println("Documentation: https://example.com")
	}
}

func setCloudsYaml(deploymentName string) {
	prompt := promptui.Select{
		Label: "Choose an option",
		Items: []string{"Set clouds_yaml", "Access documentation"},
	}
	_, result, err := prompt.Run()
	if err != nil {
		fmt.Printf("Prompt failed %v\n", err)
	}
	switch result {
	case "Set clouds_yaml":
		cmd := exec.Command("bash", "-c", `vim environment-values/`+deploymentName+`/secrets.yaml`)
		cmd.Stdin = os.Stdin
		cmd.Stdout = os.Stdout
		cmd.Run()
	case "Access documentation":
		fmt.Println("Documentation: https://example.com")
	}
}
