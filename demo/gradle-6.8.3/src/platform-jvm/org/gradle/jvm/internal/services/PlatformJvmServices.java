/*
 * Copyright 2014 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.gradle.jvm.internal.services;

import org.gradle.api.internal.artifacts.ResolveContext;
import org.gradle.api.internal.artifacts.ivyservice.ivyresolve.ComponentResolvers;
import org.gradle.api.internal.artifacts.ivyservice.ivyresolve.ResolverProviderFactory;
import org.gradle.api.internal.resolve.DefaultLocalLibraryResolver;
import org.gradle.api.internal.resolve.LocalLibraryDependencyResolver;
import org.gradle.api.internal.resolve.ProjectModelResolver;
import org.gradle.api.internal.resolve.VariantBinarySelector;
import org.gradle.internal.model.CalculatedValueContainerFactory;
import org.gradle.internal.service.ServiceRegistration;
import org.gradle.internal.service.scopes.AbstractPluginServiceRegistry;
import org.gradle.jvm.JvmBinarySpec;
import org.gradle.jvm.internal.JarBinaryRenderer;
import org.gradle.jvm.internal.resolve.DefaultJavaPlatformVariantAxisCompatibility;
import org.gradle.jvm.internal.resolve.DefaultLibraryResolutionErrorMessageBuilder;
import org.gradle.jvm.internal.resolve.DefaultVariantAxisCompatibilityFactory;
import org.gradle.jvm.internal.resolve.JvmLibraryResolveContext;
import org.gradle.jvm.internal.resolve.JvmLocalLibraryMetaDataAdapter;
import org.gradle.jvm.internal.resolve.JvmVariantSelector;
import org.gradle.jvm.internal.resolve.VariantAxisCompatibilityFactory;
import org.gradle.jvm.internal.resolve.VariantsMetaData;
import org.gradle.jvm.platform.JavaPlatform;
import org.gradle.jvm.toolchain.install.internal.AdoptOpenJdkDownloader;
import org.gradle.jvm.toolchain.install.internal.AdoptOpenJdkRemoteBinary;
import org.gradle.jvm.toolchain.install.internal.DefaultJavaToolchainProvisioningService;
import org.gradle.jvm.toolchain.install.internal.JdkCacheDirectory;
import org.gradle.jvm.toolchain.internal.AsdfInstallationSupplier;
import org.gradle.jvm.toolchain.internal.AutoInstalledInstallationSupplier;
import org.gradle.jvm.toolchain.internal.CurrentInstallationSupplier;
import org.gradle.jvm.toolchain.internal.DefaultJavaInstallationRegistry;
import org.gradle.jvm.toolchain.internal.EnvironmentVariableListInstallationSupplier;
import org.gradle.jvm.toolchain.internal.JabbaInstallationSupplier;
import org.gradle.jvm.toolchain.internal.JavaToolchainFactory;
import org.gradle.jvm.toolchain.internal.JavaToolchainQueryService;
import org.gradle.jvm.toolchain.internal.LinuxInstallationSupplier;
import org.gradle.jvm.toolchain.internal.LocationListInstallationSupplier;
import org.gradle.jvm.toolchain.internal.OsXInstallationSupplier;
import org.gradle.jvm.toolchain.internal.SdkmanInstallationSupplier;
import org.gradle.jvm.toolchain.internal.SharedJavaInstallationRegistry;
import org.gradle.jvm.toolchain.internal.WindowsInstallationSupplier;
import org.gradle.model.internal.manage.schema.ModelSchemaStore;

import java.util.Collection;
import java.util.List;

public class PlatformJvmServices extends AbstractPluginServiceRegistry {
    @Override
    public void registerGlobalServices(ServiceRegistration registration) {
        registration.add(JarBinaryRenderer.class);
        registration.add(VariantAxisCompatibilityFactory.class, DefaultVariantAxisCompatibilityFactory.of(JavaPlatform.class, new DefaultJavaPlatformVariantAxisCompatibility()));
    }

    @Override
    public void registerBuildServices(ServiceRegistration registration) {
        registration.add(DefaultJavaInstallationRegistry.class);
        registration.add(LocalLibraryDependencyResolverFactory.class);
        registration.add(JdkCacheDirectory.class);
        registration.add(SharedJavaInstallationRegistry.class);
        registerJavaInstallationSuppliers(registration);
    }

    private void registerJavaInstallationSuppliers(ServiceRegistration registration) {
        registration.add(AsdfInstallationSupplier.class);
        registration.add(AutoInstalledInstallationSupplier.class);
        registration.add(CurrentInstallationSupplier.class);
        registration.add(EnvironmentVariableListInstallationSupplier.class);
        registration.add(JabbaInstallationSupplier.class);
        registration.add(LinuxInstallationSupplier.class);
        registration.add(LocationListInstallationSupplier.class);
        registration.add(OsXInstallationSupplier.class);
        registration.add(SdkmanInstallationSupplier.class);
        registration.add(WindowsInstallationSupplier.class);
    }

    @Override
    public void registerProjectServices(ServiceRegistration registration) {
        registration.add(JavaToolchainFactory.class);
        registration.add(DefaultJavaToolchainProvisioningService.class);
        registration.add(AdoptOpenJdkRemoteBinary.class);
        registration.add(AdoptOpenJdkDownloader.class);
        registration.add(JavaToolchainQueryService.class);
    }

    private static class LocalLibraryDependencyResolverFactory implements ResolverProviderFactory {
        private final ProjectModelResolver projectModelResolver;
        private final ModelSchemaStore schemaStore;
        private final CalculatedValueContainerFactory calculatedValueContainerFactory;
        private final List<VariantAxisCompatibilityFactory> factories;

        LocalLibraryDependencyResolverFactory(ProjectModelResolver projectModelResolver, ModelSchemaStore schemaStore, CalculatedValueContainerFactory calculatedValueContainerFactory, List<VariantAxisCompatibilityFactory> factories) {
            this.projectModelResolver = projectModelResolver;
            this.schemaStore = schemaStore;
            this.calculatedValueContainerFactory = calculatedValueContainerFactory;
            this.factories = factories;
        }

        @Override
        public void create(ResolveContext context, Collection<ComponentResolvers> resolvers) {
            if (context instanceof JvmLibraryResolveContext) {
                VariantsMetaData variants = ((JvmLibraryResolveContext) context).getVariants();
                VariantBinarySelector variantSelector = new JvmVariantSelector(factories, JvmBinarySpec.class, schemaStore, variants);
                JvmLocalLibraryMetaDataAdapter libraryMetaDataAdapter = new JvmLocalLibraryMetaDataAdapter();
                resolvers.add(new LocalLibraryDependencyResolver(
                    JvmBinarySpec.class,
                    projectModelResolver,
                    new DefaultLocalLibraryResolver(),
                    variantSelector,
                    libraryMetaDataAdapter,
                    new DefaultLibraryResolutionErrorMessageBuilder(variants, schemaStore),
                    calculatedValueContainerFactory
                ));
            }
        }
    }
}
