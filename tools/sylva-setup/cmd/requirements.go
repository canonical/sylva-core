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
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/docker/docker/api/types/network"
	"github.com/docker/docker/client"
	"github.com/manifoldco/promptui"
	"github.com/pkg/browser"
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
		binaries := []string{"git", "yq", "vimT"}
		fmt.Printf("Checking for required common binaries: %s\n", binaries)
		checkBinaries(binaries)

		time.Sleep(2 * time.Second)

		if contains(args, "docker") {
			fmt.Println("Checking for docker client binary")
			checkBinaries([]string{"docker"})
			fmt.Println("Checking for kind network...")
			checkKindNetwork()
		} else if contains(args, "openstack") {
			fmt.Println("Checking for openstack client binary")
			checkBinaries([]string{"openstack"})
			fmt.Println("Checking for openstack clouds.yaml")
			checkCloudsYaml()
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
			for {
				prompt := promptui.Prompt{
					Label:     fmt.Sprintf("Would you like to install %s?: ", binary),
					IsConfirm: true,
					Default:   "y",
				}
				validate := func(s string) error {
					if len(s) == 1 && strings.Contains("yYnN", s) || prompt.Default != "" && len(s) == 0 {
						return nil
					}
					return errors.New("invalid input")
				}
				prompt.Validate = validate

				result, err := prompt.Run()
				confirmed := !errors.Is(err, promptui.ErrAbort)
				if err != nil && confirmed {
					fmt.Println("ERROR: ", err)
					continue
				}

				result = strings.ToLower(strings.TrimSpace(result))

				if result == "y" {
					installCommand := exec.Command("apt-get", "install", "-y", binary)
					err := installCommand.Run()
					if err != nil {
						fmt.Printf("Failed to install %s: %s\n", binary, err)
					} else {
						fmt.Printf("%s has been installed\n", binary)
					}
				} else if result == "n" {
					fmt.Printf("You'll need %s before continuing\n", binary)
					break
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
	creatingKindNetwork()
}

func creatingKindNetwork() {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		panic(err)
	}

	fmt.Print("Creating kind network...\n")
	res, _ := cli.NetworkCreate(context.Background(), "kind", network.CreateOptions{})
	ip, _ := cli.NetworkInspect(context.Background(), res.ID, network.InspectOptions{})
	fmt.Print(ip.IPAM.Config[0].Subnet)
}

func checkCloudsYaml() {
	userDir, err := os.UserHomeDir()
	if err != nil {
		fmt.Printf("Failed to get user directory: %s\n", err)
		return
	}
	paths := []string{"clouds.yaml", "/etc/openstack/clouds.yaml"}
	paths = append(paths, fmt.Sprintf("%s/.confieeg/openstack/clouds.yaml", userDir))
	for _, path := range paths {
		if _, err := os.Stat(path); err == nil {
			fmt.Printf("%s found\n", path)
			return
		}
	}

	createCloudsYaml()
}

func createCloudsYaml() {
	prompt := promptui.Select{
		Label: "clouds.yaml not found. What would you like to do?",
		Items: []string{"Go to the documentation", "Create clouds.yaml in current directory", "Exit"},
	}

	_, result, err := prompt.Run()
	if err != nil {
		fmt.Printf("Failed to read user input: %s\n", err)
		return
	}

	switch result {
	case "Go to the documentation":
		const url = "https://docs.openstack.org/python-openstackclient/pike/configuration/index.html#clouds-yaml"
		browser.OpenURL(url)

		prompt.Items = []string{"Create clouds.yaml in current directory", "Exit"}
		_, _, err = prompt.Run()
		if err != nil {
			fmt.Printf("Failed to read user input: %s\n", err)
			return
		}

	case "Create clouds.yaml in current directory":
		templatePath := "./templates/clouds.yaml"
		destPath := "clouds.yaml"

		cpCmd := exec.Command("cp", "-rf", templatePath, destPath)
		err := cpCmd.Run()
		if err != nil {
			fmt.Printf("Failed to copy template file: %s\n", err)
		}

		openWithVim(destPath)

		return

		// Copy the template file
		/*
			_, err := io.Copy(templatePath, destPath)
			if err != nil {
				fmt.Printf("Failed to copy template file: %s\n", err)
				return
			}

			// Open the copied file with vim
			err = openWithVim(destPath)
			if err != nil {
				fmt.Printf("Failed to open file with vim: %s\n", err)
				return
			}

			fmt.Println("clouds.yaml created and opened with vim successfully")

			/* err := os.WriteFile("clouds.yaml", []byte(cloudsYamlContent), 0600)
			if err != nil {
				fmt.Printf("Failed to create clouds.yaml: %s\n", err)
				return
			}
			fmt.Println("clouds.yaml created successfully") */

	case "Exit":
		return
	}
}

func openWithVim(path string) error {
	cmd := exec.Command("vim", path)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
