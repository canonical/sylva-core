/*
Copyright © 2024 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"archive/tar"
	"compress/gzip"
	"github.com/spf13/cobra"
)

// readyCmd represents the ready command
var readyCmd = &cobra.Command{
	Use:   "ready",
	Short: "A brief description of your command",
	Long: `A longer description that spans multiple lines and likely contains examples
and usage of using your command. For example:

Cobra is a CLI library for Go that empowers applications.
This application is a tool to generate the needed files
to quickly create a Cobra application.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("ready called")
		hello_world()
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
	tu arrives chez Orange/TelecomItalia/etc., tu dois installer sylva

	install les requirements
	git clone sylvacore  (main)
	print ouvre la doc

}


// downloadFile downloads a file from a URL and saves it to a local path.
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

// extractTarGz extracts a .tar.gz file to a specified destination.
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

// installPackage installs a package using apt-get.
func installPackage(pkg string) error {
	cmd := exec.Command("sudo", "apt-get", "install", "-y", pkg)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// isInstalled checks if a binary is installed.
func isInstalled(binary string) bool {
	_, err := exec.LookPath(binary)
	return err == nil
}

// installPackages installs the required packages.
func installPackages() error {
	packages := map[string]string{
		"apt":        "apt",
		"python3":    "python3",
		"git":        "git",
		"docker.io":  "docker",
		"yq":         "yq",
		"yamllint":   "yamllint",
		"pip3":       "python3-pip",
		"PyYAML":     "pip3 install PyYAML",
	}

	for binary, pkg := range packages {
		if isInstalled(binary) {
			fmt.Printf("%s is already installed\n", binary)
		} else {
			fmt.Printf("Installing %s...\n", pkg)
			if binary == "PyYAML" {
				cmd := exec.Command("pip3", "install", "PyYAML")
				cmd.Stdout = os.Stdout
				cmd.Stderr = os.Stderr
				if err := cmd.Run(); err != nil {
					return fmt.Errorf("failed to install %s: %w", binary, err)
				}
			} else {
				if err := installPackage(pkg); err != nil {
					return fmt.Errorf("failed to install %s: %w", binary, err)
				}
			}
		}
	}

	// Check and install k9s
	if isInstalled("k9s") {
		fmt.Println("k9s is already installed")
	} else {
		k9sURL := "https://github.com/derailed/k9s/releases/download/v0.32.5/k9s_Freebsd_amd64.tar.gz"
		k9sDest := "/tmp/k9s_Freebsd_amd64.tar.gz"
		fmt.Println("Downloading k9s...")
		if err := downloadFile(k9sURL, k9sDest); err != nil {
			return fmt.Errorf("failed to download k9s: %w", err)
		}
		fmt.Println("Extracting k9s...")
		if err := extractTarGzFile(k9sDest, "/usr/local/bin"); err != nil {
			return fmt.Errorf("failed to extract k9s: %w", err)
		}
	}

	return nil
}

