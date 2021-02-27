/*
 * Copyright 2020 the original author or authors.
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

package org.gradle.configurationcache.serialization.codecs.transform

import org.gradle.api.artifacts.transform.TransformParameters
import org.gradle.api.internal.artifacts.transform.ArtifactTransformParameterScheme
import org.gradle.api.internal.artifacts.transform.DefaultTransformer
import org.gradle.api.internal.file.FileCollectionFactory
import org.gradle.api.internal.initialization.RootScriptDomainObjectContext
import org.gradle.configurationcache.extensions.uncheckedCast
import org.gradle.configurationcache.serialization.Codec
import org.gradle.configurationcache.serialization.ReadContext
import org.gradle.configurationcache.serialization.WriteContext
import org.gradle.internal.hash.ClassLoaderHierarchyHasher
import org.gradle.internal.isolation.IsolatableFactory
import org.gradle.internal.operations.BuildOperationExecutor
import org.gradle.internal.snapshot.ValueSnapshotter


class IsolateTransformerParametersNodeCodec(
    val parameterScheme: ArtifactTransformParameterScheme,
    val isolatableFactory: IsolatableFactory,
    val buildOperationExecutor: BuildOperationExecutor,
    val classLoaderHierarchyHasher: ClassLoaderHierarchyHasher,
    val valueSnapshotter: ValueSnapshotter,
    val fileCollectionFactory: FileCollectionFactory
) : Codec<DefaultTransformer.IsolateTransformerParameters> {
    override suspend fun WriteContext.encode(value: DefaultTransformer.IsolateTransformerParameters) {
        write(value.parameterObject)
        writeClass(value.implementationClass)
        writeBoolean(value.isCacheable)
    }

    override suspend fun ReadContext.decode(): DefaultTransformer.IsolateTransformerParameters? {
        val parameterObject: TransformParameters? = read()?.uncheckedCast()
        val implementationClass = readClass()
        val cacheable = readBoolean()

        return DefaultTransformer.IsolateTransformerParameters(
            parameterObject,
            implementationClass,
            cacheable,
            RootScriptDomainObjectContext.INSTANCE,
            parameterScheme.inspectionScheme.propertyWalker,
            isolatableFactory,
            buildOperationExecutor,
            classLoaderHierarchyHasher,
            valueSnapshotter,
            fileCollectionFactory
        )
    }
}
