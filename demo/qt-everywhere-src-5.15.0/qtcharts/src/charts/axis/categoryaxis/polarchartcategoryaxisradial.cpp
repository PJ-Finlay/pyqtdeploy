/****************************************************************************
**
** Copyright (C) 2016 The Qt Company Ltd.
** Contact: https://www.qt.io/licensing/
**
** This file is part of the Qt Charts module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:GPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3 or (at your option) any later version
** approved by the KDE Free Qt Foundation. The licenses are as published by
** the Free Software Foundation and appearing in the file LICENSE.GPL3
** included in the packaging of this file. Please review the following
** information to ensure the GNU General Public License requirements will
** be met: https://www.gnu.org/licenses/gpl-3.0.html.
**
** $QT_END_LICENSE$
**
****************************************************************************/

#include <private/polarchartcategoryaxisradial_p.h>
#include <private/chartpresenter_p.h>
#include <private/abstractchartlayout_p.h>
#include <QtCharts/QCategoryAxis>
#include <QtCore/QDebug>

QT_CHARTS_BEGIN_NAMESPACE

PolarChartCategoryAxisRadial::PolarChartCategoryAxisRadial(QCategoryAxis *axis, QGraphicsItem *item)
    : PolarChartAxisRadial(axis, item, true)
{
    QObject::connect(axis, SIGNAL(categoriesChanged()), this, SLOT(handleCategoriesChanged()));
}

PolarChartCategoryAxisRadial::~PolarChartCategoryAxisRadial()
{
}

QVector<qreal> PolarChartCategoryAxisRadial::calculateLayout() const
{
    QCategoryAxis *catAxis = static_cast<QCategoryAxis *>(axis());
    int tickCount = catAxis->categoriesLabels().count() + 1;
    QVector<qreal> points;

    if (tickCount < 2)
        return points;

    qreal range = max() - min();
    if (range > 0) {
        points.resize(tickCount);
        qreal scale = (axisGeometry().width() / 2) / range;
        qreal angle;
        for (int i = 0; i < tickCount; ++i) {
            if (i < tickCount - 1)
                angle = (catAxis->startValue(catAxis->categoriesLabels().at(i)) - min()) * scale;
            else
                angle = (catAxis->endValue(catAxis->categoriesLabels().at(i - 1)) - min()) * scale;
            points[i] = angle;
        }
    }

    return points;
}

void PolarChartCategoryAxisRadial::createAxisLabels(const QVector<qreal> &layout)
{
    Q_UNUSED(layout);
    setLabels(static_cast<QCategoryAxis *>(axis())->categoriesLabels() << QString());
}

void PolarChartCategoryAxisRadial::handleCategoriesChanged()
{
    QGraphicsLayoutItem::updateGeometry();
    presenter()->layout()->invalidate();
}

QT_CHARTS_END_NAMESPACE

#include "moc_polarchartcategoryaxisradial_p.cpp"