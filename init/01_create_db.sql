-- Script 01: Crear base de datos
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'PruebaNomina')
BEGIN
    CREATE DATABASE PruebaNomina;
END
GO
