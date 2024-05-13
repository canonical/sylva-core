package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"

	"github.com/bitfield/script"
	kustomizev1 "github.com/fluxcd/kustomize-controller/api/v1"
)

var (
	// source: https://www.reddit.com/r/golang/comments/12rm094/comment/jgvxttj/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
	Scheme = runtime.NewScheme()
	Codecs = serializer.NewCodecFactory(Scheme)
)

func extractDependency(suPath string, clusterType string, clusterFlavor string) []string {
	// register the imported kubernetes type, to unmarshall slice of bytes to Kustomization.kustomize.toolkit.fluxcd.io
	kustomizev1.AddToScheme(Scheme)

	diagramText := []string{}

	// source: https://pkg.go.dev/github.com/bitfield/script#Pipe.String
	// helmTemplate, err := script.Exec("helm template ../../charts/sylva-units/ --values ../../charts/sylva-units/values.yaml --values ../../charts/sylva-units/management.values.yaml --values ../../charts/sylva-units/bootstrap.values.yaml -s templates/units.yaml").String()

	var clusterTypeValues string
	clusterFlavorValues := " --values ../../environment-values/" + clusterFlavor + "/values.yaml" + " --values ../../environment-values/" + clusterFlavor + "/secrets.yaml"
	switch clusterType {
	case "bootstrap":
		clusterTypeValues = " --values management.values.yaml --values bootstrap.values.yaml"
	case "management":
		clusterTypeValues = " --values management.values.yaml"
	case "workload":
		clusterTypeValues = " --values workload-cluster.values.yaml"
		clusterFlavorValues = clusterFlavorValues + " --values ../../environment-values/workload-clusters/" + clusterFlavor + "/values.yaml" + " --values ../../environment-values/workload-clusters/" + clusterFlavor + "/secrets.yaml" + " --values test-values/workload-cluster/shared-settings-mock.values.yaml"
	default:
		fmt.Println("Unknown sylva cluster type")
	}

	// no way to run script.Exec() from different dir: https://github.com/bitfield/script/issues/112
	// os.Chdir() is system wide, both script.Exec() and os.Create() for writing to file change dir
	os.Chdir(suPath)
	helmArg := " . --values values.yaml" + clusterTypeValues + clusterFlavorValues + " -s templates/units.yaml"
	fmt.Println("\n Parsing output of: \n\t" + "helm template" + helmArg)
	helmTemplate, err := script.Exec("helm template" + helmArg).String()

	// helmTemplate, err := script.Exec("helm template . --values values.yaml --values management.values.yaml --values bootstrap.values.yaml -s templates/units.yaml").Stdout()
	if err != nil {
		panic(err)
	}
	// Split the YAML data from helm template into individual Kubernetes manifests
	// by checking for "---" appearing after a newline character
	manifests := strings.Split(string(helmTemplate), "\n---")

	// Parse each Kubernetes manifest
	for _, manifest := range manifests {
		manifestByteArray := []byte(manifest)
		// Parse the YAML into a custom struct
		obj, _, err := Codecs.UniversalDeserializer().Decode(manifestByteArray, nil, nil)

		if err != nil {
			log.Println(fmt.Sprintf("Error while decoding YAML object. Err was: %s", err))
			continue
		}

		// Process the parsed manifest
		// fmt.Println(reflect.TypeOf(obj)) // *v1.Kustomization

		// obj holds the decoded Kubernetes object, but its type is runtime.Object
		// which is an interface representing any Kubernetes API object.
		// We need to assert obj to type *v1.Kustomization
		kustomization, ok := obj.(*kustomizev1.Kustomization)
		if !ok {
			fmt.Println("Error: Failed to assert obj to *v1.Kustomization")
			continue
		}

		fmt.Println("Parsing Kustomization " + kustomization.Name + " for elements of ks.spec.dependsOn")
		for _, dependency_unit := range kustomization.Spec.DependsOn {
			// fmt.Println(reflect.TypeOf(dependency_unit)) // meta.NamespacedObjectReference
			// fmt.Printf("%s\n", dependency_unit.Name)
			diagramText = append(diagramText, "  "+dependency_unit.Name+" --> "+kustomization.Name)
		}
	}
	return diagramText
}
