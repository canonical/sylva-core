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
	"context"
	"fmt"
	"os/exec"

	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
)

// requirementsCmd represents the requirements command
var requirementsCmd = &cobra.Command{
	Use:     "requirements",
	Aliases: []string{"req"},
	Short:   "A brief description of your command",
	Long: `A longer description that spans multiple lines and likely contains examples
and usage of using your command. For example:

Cobra is a CLI library for Go that empowers applications.
This application is a tool to generate the needed files
to quickly create a Cobra application.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Command Requirements called")
		fmt.Print("Checking for required binaries...\n")
		binaries := []string{"git", "yq", "vimT"}
		for _, binary := range binaries {
			fmt.Println(binary)
		}
		checkBinaries(binaries)

		if contains(args, "docker") {
			fmt.Println("Checking for kind network...")
			checkKindNetwork()
		}
	},
}

func contains(slice []string, str string) bool {
	for _, s := range slice {
		if s == str {
			return true
		}
	}
	return false
}

func init() {
	rootCmd.AddCommand(requirementsCmd)
}

func checkBinaries(binaries []string) {
	for _, binary := range binaries {
		_, err := exec.LookPath(binary)
		if err != nil {
			fmt.Printf("%s is not installed\n", binary)
			prompt := promptui.Prompt{
				Label:     fmt.Sprintf("Would you like to install %s? (y/n): ", binary),
				IsConfirm: true,
			}
			result, err := prompt.Run()
			if err != nil {
				fmt.Printf("Failed to read user input: %s\n", err)
				continue
			}
			if result == "y" || result == "Y" {
				installCommand := exec.Command("apt-get", "install", "-y", binary)
				err := installCommand.Run()
				if err != nil {
					fmt.Printf("Failed to install %s: %s\n", binary, err)
				} else {
					fmt.Printf("%s has been installed\n", binary)
				}
			}
		} else {
			fmt.Printf("%s is installed\n", binary)
		}
	}
}

func checkKindNetwork() {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		panic(err)
	}

	networks, err := cli.NetworkList(context.Background(), network.ListOptions{})
	if err != nil {
		panic(err)
	}

	for _, ctr := range networks {
		if ctr.Name == "kind" {
			fmt.Println("Kind network found")
			fmt.Printf("%s %s\n", ctr.IPAM.Config[0].Subnet, ctr.Name)
			return
		}
	}

	fmt.Print("Kind network not found\n")
	fmt.Print("Creating kind network...\n")
	res, _ := cli.NetworkCreate(context.Background(), "kind", network.CreateOptions{})
	fmt.Print(res)
}
