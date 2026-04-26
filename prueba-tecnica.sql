-- =========================================================================
-- Script de Base de Datos para Prueba Técnica 
-- Motor: SQL Server (Puedes usar el motor que desees)
-- Objetivo: Creación de entorno y tabla transaccional para POC de Nómina
-- =========================================================================

-- 1. Creación de la Base de Datos (Entorno de pruebas)
CREATE DATABASE PruebaNomina;
GO

USE PruebaNomina;
GO

-- 2. Creación de la tabla transaccional destino
CREATE TABLE Novedades_HorasExtras (
    IdNovedad INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Campos provenientes de la extracción (CSV)
    DocumentoEmpleado VARCHAR(20) NOT NULL,
    TipoHoraExtra VARCHAR(50) NOT NULL,
    CantidadHoras DECIMAL(5,2) NOT NULL,
    FechaReporte DATE NOT NULL,
    
    -- Campos de auditoría generados por el sistema/script
    FechaProcesamiento DATETIME DEFAULT GETDATE(),
    EstadoValidacion VARCHAR(20) DEFAULT 'EXITOSO'
);
GO

-- =========================================================================
-- NOTA PARA EL CANDIDATO: 
-- Solo deben llegar a esta tabla los registros que pasen exitosamente 
-- las reglas de negocio estipuladas en las instrucciones.
-- =========================================================================