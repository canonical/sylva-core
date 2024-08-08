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
	"archive/tar"
	"compress/gzip"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/manifoldco/promptui"
	"github.com/spf13/cobra"
)

// readyCmd represents the ready command
var readyCmd = &cobra.Command{
	Use:   "ready",
	Short: "Set up your development environment",
	Long: `This command sets up your development environment by installing necessary packages and
cloning Sylva Git repository.`,
	Run: func(cmd *cobra.Command, args []string) {
		hello_world()
		setupDevEnv()
		// if err := setupDevEnv(); err != nil {
		// 	mt.Printf("Error: %v\n", err)
		// 	os.Exit(1)
		// }
		// fmt.Println("Your dev environment is ready. If you don't know what to do next, you can go to the doc <link to the doc>")
	},
}

func init() {
	devCmd.AddCommand(readyCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// readyCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// readyCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

func hello_world() {
	fmt.Println("Hello world.")
}

type Package struct {
	Name string
	// Version string
	Type    string
	Command string
	URL     string
}

func setupDevEnv() error {
	packages := []Package{
		// name, version, type, command, url
		{Name: "python3", Type: "apt", Command: "python3"},
		{Name: "git", Type: "apt", Command: "git"},
		{Name: "docker.io", Type: "apt", Command: "docker"},
		{Name: "yamllint", Type: "apt", Command: "yamllint"},
		{Name: "ca-certificates", Type: "apt"},
		{Name: "gnupg", Type: "apt"},
		{Name: "binutils", Type: "apt"},
		{Name: "lsb-release", Type: "apt", Command: "lsb_release"},
		{Name: "tar", Type: "apt"},

		{Name: "PyYAML", Type: "pip"},
		{Name: "python-openstackclient", Type: "pip", Command: "openstack"}, //Version: "6.4.0"
		{Name: "python-heatclient", Type: "pip", Command: "openstack"},

		{Name: "crictl", Type: "go-binary", Command: "crictl", URL: "https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.30.0/crictl-v1.30.0-linux-amd64.tar.gz"}, //Version: "1.30.0"

		{Name: "vimA", Type: "apt", Command: "vimA"},
		{Name: "vimPy55", Type: "pip", Command: "vimP"},
		{Name: "vimG", Type: "go-binary", Command: "vimG", URL: "https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.30.0/crictl-$VERSION-linux-amd64.tar.gz"}, //Version: "1.30.0"

		//already shipped within sylva-core/bin
		// {Name: "yq", Type: "apt", Command: "yq"},
		// {Name: "k9s", Type: "go-binary", Command: "k9s", URL: "https://github.com/derailed/k9s/releases/download/v0.32.5/k9s_Freebsd_amd64.tar.gz"}, //Version: "0.32.5"
	}

	installed, notInstalled := checkPackages(packages)

	fmt.Println("Installed packages:")
	for _, pkg := range installed {
		fmt.Println("-", pkg.Name)
	}

	fmt.Println("\nNot installed packages:")
	for _, pkg := range notInstalled {
		fmt.Println("-", pkg.Name)
	}

	prompt := promptui.Prompt{
		Label:     "Would you like to install all missing packages? (y/n)",
		IsConfirm: true,
	}

	result, err := prompt.Run()
	if err != nil {
		fmt.Printf("Failed to read user input: %s\n", err)
	}

	if result != "y" && result != "Y" {
		fmt.Println("You'll need those package to continue. Exiting...")
		return nil
	}

	var errors []string

	// Run apt-get update
	if err := runCommand("sudo", []string{"apt-get", "update", "-y"}); err != nil {
		fmt.Printf("Error executing 'apt-get update': %v\n", err)
		return nil
	}

	// Run apt-get upgrade
	if err := runCommand("sudo", []string{"apt-get", "upgrade", "-y"}); err != nil {
		fmt.Printf("Error executing 'apt-get upgrade': %v\n", err)
		return nil
	}
	userBinDir := filepath.Join(os.Getenv("HOME"), "bin")

	// Install packages
	for _, pkg := range notInstalled {
		if err := installPackage(pkg); err != nil {
			errors = append(errors, fmt.Sprintf("failed to install %s: %v", pkg.Name, err))
		}
	}

	// Clone or update Sylva Repo
	fmt.Println("Cloning or updating Sylva-Core Git repository...")
	if err := cloneOrUpdateRepository("https://gitlab.com/sylva-projects/sylva-core.git", "sylva-core"); err != nil {
		errors = append(errors, fmt.Sprintf("failed to clone or update repository: %v", err))
	}

	// Run the Docker command to fetch sylva-toolbox
	dockerCmd := "sudo"
	dockerArgs := []string{"docker", "run", "--rm", "registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.5.5"}
	tarCmd := "sudo"
	tarArgs := []string{"tar", "xzv", "-C", userBinDir}

	if err := runPipedCommands(dockerCmd, dockerArgs, tarCmd, tarArgs); err != nil {
		fmt.Printf("Error executing Docker command: %v\n", err)
		os.Exit(1)
	}

	// Get the absolute path to the cloned repository
	if err != nil {
		errors = append(errors, fmt.Sprintf("failed to get current working directory: %v", err))
	} else {
		// Get shell config path
		shellConfigPath, err := detectShellConfigPath()
		if err != nil {
			errors = append(errors, fmt.Sprintf("failed to detect shell configuration path: %v", err))
		} else {
			// Append the source command to the shell config file
			sourceCommand := fmt.Sprintf("source %s/bin/env", userBinDir)
			if err := appendToShellConfig(shellConfigPath, sourceCommand); err != nil {
				errors = append(errors, fmt.Sprintf("failed to append to shell configuration file: %v", err))
			}

			// Append the export PATH command to the shell config file
			exportPathCommand := fmt.Sprintf("export PATH=$PATH:%s", userBinDir)
			if err := appendToShellConfig(shellConfigPath, exportPathCommand); err != nil {
				errors = append(errors, fmt.Sprintf("failed to append export PATH command to shell configuration file: %v", err))
			}

		}
	}

	if len(errors) > 0 {
		fmt.Println("The following errors occurred during setup:")
		for _, err := range errors {
			fmt.Println("-", err)
		}
		fmt.Println("Please review the errors, verify your network and environment settings, and then rerun the script.")
	} else {
		fmt.Println("Please source your shell configuration file to complete the setup of your development environment.")
	}
	return nil
}

func checkPackages(packages []Package) (installed, notInstalled []Package) {
	for _, pkg := range packages {
		if isInstalled(pkg) {
			installed = append(installed, pkg)
		} else {
			notInstalled = append(notInstalled, pkg)
		}
	}
	return
}

func isInstalled(pkg Package) bool {
	var cmd string
	var args []string

	switch pkg.Type {
	case "apt":
		cmd = "dpkg-query"
		args = []string{"-W", "-f='${Status}'", pkg.Name}
	case "pip":
		cmd = "pip3"
		args = []string{"show", pkg.Name}
	case "go-binary":
		_, err := exec.LookPath(pkg.Command)
		return err == nil
	default:
		fmt.Printf("Unknown package type: %s\n", pkg.Type)
		return false
	}

	// Execute the command and check the output
	output, err := exec.Command(cmd, args...).CombinedOutput()
	if err != nil {
		return false
	}

	// For apt packages, check if the output contains "install ok installed"
	if pkg.Type == "apt" {
		return string(output) == "'install ok installed'"
	}

	// For pip packages, any output means the package is installed
	return true
}

func installPackage(pkg Package) error {
	fmt.Printf("Installing %s...\n", pkg.Name)
	switch pkg.Type {
	case "apt":
		return runCommand("sudo", []string{"apt-get", "install", "-y", pkg.Name})
	case "pip":
		return runCommand("pip3", []string{"install", pkg.Name})
	case "go-binary":
		dest := "/tmp/" + filepath.Base(pkg.URL)
		if err := downloadFile(pkg.URL, dest); err != nil {
			return err
		}
		userBinDir := filepath.Join(os.Getenv("HOME"), "bin")
		if err := os.MkdirAll(userBinDir, 0755); err != nil {
			return err
		}
		return extractTarGzFile(dest, userBinDir)
	default:
		return fmt.Errorf("unknown package type: %s", pkg.Type)
	}
}

func downloadFile(url, dest string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	out, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, resp.Body)
	return err
}

func extractTarGzFile(src, dest string) error {
	file, err := os.Open(src)
	if err != nil {
		return err
	}
	defer file.Close()

	return extractTarGz(file, dest)
}

func extractTarGz(gzipStream io.Reader, dest string) error {
	uncompressedStream, err := gzip.NewReader(gzipStream)
	if err != nil {
		return err
	}
	tarReader := tar.NewReader(uncompressedStream)

	for {
		header, err := tarReader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		target := filepath.Join(dest, header.Name)
		switch header.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(target, 0755); err != nil {
				return err
			}
		case tar.TypeReg:
			outFile, err := os.Create(target)
			if err != nil {
				return err
			}
			if _, err := io.Copy(outFile, tarReader); err != nil {
				return err
			}
			outFile.Close()
			if err := os.Chmod(target, 0755); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unknown type: %v in %s", header.Typeflag, header.Name)
		}
	}
	return nil
}

func cloneOrUpdateRepository(repoURL, dest string) error {
	if _, err := os.Stat(dest); os.IsNotExist(err) {
		// Directory does not exist, clone the repository
		fmt.Printf("Cloning repository %s to %s...\n", repoURL, dest)
		return runCommand("git", []string{"clone", repoURL, dest})
	} else {
		// Directory exists, pull the latest changes
		fmt.Printf("Repository already exists at %s. Pulling latest changes...\n", dest)
		return runCommand("git", []string{"-C", dest, "pull", "origin", "main"})
	}
}

func appendToShellConfig(shellConfigPath, command string) error {
	// Read the existing content of the shell configuration file
	content, err := os.ReadFile(shellConfigPath)
	if err != nil && !os.IsNotExist(err) {
		return err
	}

	// Check if the command is already present
	if strings.Contains(string(content), command) {
		fmt.Println("The command is already present in the shell configuration file.")
		return nil
	}

	// Open the file for appending
	file, err := os.OpenFile(shellConfigPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer file.Close()

	// Append the command to the file
	if _, err := file.WriteString(command + "\n"); err != nil {
		return err
	}

	return nil
}

func detectShellConfigPath() (string, error) {
	userShell := os.Getenv("SHELL")
	if userShell == "" {
		return "", fmt.Errorf("could not detect the user's shell")
	}

	switch filepath.Base(userShell) {
	case "bash":
		return filepath.Join(os.Getenv("HOME"), ".bashrc"), nil
	case "zsh":
		return filepath.Join(os.Getenv("HOME"), ".zshrc"), nil
	default:
		return "", fmt.Errorf("unsupported shell: %s", userShell)
	}
}

func runCommand(cmd string, args []string) error {
	command := exec.Command(cmd, args...)
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	return command.Run()
}

func runPipedCommands(cmd1 string, args1 []string, cmd2 string, args2 []string) error {
	command1 := exec.Command(cmd1, args1...)
	command2 := exec.Command(cmd2, args2...)

	// Pipe the output of command1 to the input of command2
	pipe, err := command1.StdoutPipe()
	if err != nil {
		return err
	}
	command2.Stdin = pipe

	// Start command1
	if err := command1.Start(); err != nil {
		return err
	}

	// Start command2
	if err := command2.Start(); err != nil {
		return err
	}

	// Wait for command1 to finish
	if err := command1.Wait(); err != nil {
		return err
	}

	// Wait for command2 to finish
	return command2.Wait()
}
