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
		if err := setupDevEnv(); err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("Your dev environment is ready. If you don't know what to do next, you can go to the doc <link to the doc>")
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
	Name   string
	Type   string
	URL    string
	Binary string
}

func init() {
	devCmd.AddCommand(readyCmd)
}

func setupDevEnv() error {
	// name, type, url, command
	packages := []Package{
		{"apt", "apt", "", "apt"},
		{"python3", "apt", "", "python3"},
		{"git", "apt", "", "git"},
		{"docker.io", "apt", "", "docker"},
		{"yq", "apt", "", "yq"},
		{"yamllint", "apt", "", "yamllint"},
		{"pip3", "apt", "", "pip3"},
		{"PyYAML", "pip", "", "pyyaml"},
		{"k9s", "go-binary", "https://github.com/derailed/k9s/releases/download/v0.32.5/k9s_Freebsd_amd64.tar.gz", "k9s"},
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
		return fmt.Errorf("failed to read user input: %w", err)
	}
	fmt.Println(result)
	if result != "y" {
		fmt.Println("You'll need those package to continue. Exiting...")
		return nil
	}

	fmt.Println("downloading packages...")
	// for _, pkg := range notInstalled {
	// 	if err := installPackage(pkg); err != nil {
	// 		return fmt.Errorf("failed to install %s: %w", pkg.Name, err)
	// 	}
	// }
	fmt.Println("cloning sylva core repository...")
	// if err := cloneRepository("https://gitlab.com/sylva-projects/sylva-core.git", "sylva-core"); err != nil {
	// 	return fmt.Errorf("failed to clone repository: %w", err)
	// }

	return nil
}

func checkPackages(packages []Package) (installed, notInstalled []Package) {
	for _, pkg := range packages {
		if isInstalled(pkg.Name) {
			installed = append(installed, pkg)
		} else {
			notInstalled = append(notInstalled, pkg)
		}
	}
	return
}

func isInstalled(binary string) bool {
	_, err := exec.LookPath(binary)
	return err == nil
}

func installPackage(pkg Package) error {
	fmt.Printf("Installing %s...\n", pkg.Name)
	switch pkg.Type {
	case "apt":
		return exec.Command("sudo", "apt-get", "install", "-y", pkg.Name).Run()
	case "pip":
		return exec.Command("pip3", "install", pkg.Name).Run()
	case "go-binary":
		dest := "/tmp/" + filepath.Base(pkg.URL)
		if err := downloadFile(pkg.URL, dest); err != nil {
			return err
		}
		return extractTarGzFile(dest, "/usr/local/bin")
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
		default:
			return fmt.Errorf("unknown type: %v in %s", header.Typeflag, header.Name)
		}
	}
	return nil
}

func cloneRepository(repoURL, dest string) error {
	fmt.Printf("Cloning repository %s to %s...\n", repoURL, dest)
	cmd := exec.Command("git", "clone", repoURL, dest)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
