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
		Long:    `This command will guide the user to initialize a new sylva deployment.`,
		Run: func(cmd *cobra.Command, args []string) {
			// fmt.Println("init called")

			bootstrapprovider = chooseBootstrapProvider()
			infraprovider = chooseInfraProvider()
			genericName = bootstrapprovider + "-" + infraprovider
			deploymentName := chooseDeploymentName("sylva-" + genericName)

			fmt.Println(`
			====================================
					   Initialization
			====================================`)
			fmt.Println("You choose the following options:")
			fmt.Println("  - Bootstrap Provider:", bootstrapprovider)
			fmt.Println("  - Infrastructure Provider:", infraprovider)
			fmt.Println("  - Deployment Name:", deploymentName)
			fmt.Println(`
			====================================`)

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

				printWarnings(bootstrapprovider, infraprovider)

				// fmt.Println("Values copied successfully in /environment-values/" + deploymentName)
			} else {
				fmt.Println("Initialization aborted")
			}
		},
	}
)

func init() {
	rootCmd.AddCommand(initCmd)

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

func printWarnings(bootstrapProvider string, infraProvider string) {
	fmt.Println(`
	====================================
			   General Warnings
	====================================`)
	fmt.Println("  - Make sure you have set the necessary proxies")


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
		fmt.Println(`
	====================================
			   CAPD WARNINGS
	====================================`)
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
	} else if infraProvider == "capv" {
		fmt.Println(`
	====================================
			   CAPV WARNINGS			
	====================================`)
	}
}
